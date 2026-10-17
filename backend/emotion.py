import os
import torch
from huggingface_hub import hf_hub_download
from transformers import AutoTokenizer, Wav2Vec2FeatureExtractor, ViTImageProcessor
import librosa
import numpy as np
from PIL import Image

print("Loading model and weights into memory once...")
REPO_ID = "jihedjabnoun/egcaf-meld"

model_def_path = hf_hub_download(repo_id=REPO_ID, filename="modeling_hybrid.py")
model_path = hf_hub_download(repo_id=REPO_ID, filename="pytorch_model.bin")

exec(open(model_def_path).read())

model = HybridLateFusionToEarlyFusion(
    num_labels=7,
    hidden_size=512,
    num_heads=8,
    freeze_experts=True,
)

state_dict = torch.load(model_path, map_location="cpu")
new_state_dict = {}

for k, v in state_dict.items():
    new_k = k
    if "vision_expert.vit" in new_k:
        new_k = new_k.replace("encoder.layer.", "layers.")
        new_k = new_k.replace("attention.attention.query.", "attention.q_proj.")
        new_k = new_k.replace("attention.attention.key.", "attention.k_proj.")
        new_k = new_k.replace("attention.attention.value.", "attention.v_proj.")
        new_k = new_k.replace("attention.output.dense.", "attention.o_proj.")
        new_k = new_k.replace("intermediate.dense.", "mlp.fc1.")
        new_k = new_k.replace("output.dense.", "mlp.fc2.")
    new_state_dict[new_k] = v

model.load_state_dict(new_state_dict)
model.eval()

text_tokenizer = AutoTokenizer.from_pretrained("jihedjabnoun/text-emotion-distilroberta")
audio_extractor = Wav2Vec2FeatureExtractor.from_pretrained("jihedjabnoun/hubert-emotion-recognition-v2")
vision_processor = ViTImageProcessor.from_pretrained("jihedjabnoun/vit-face-emotion-recognition")
print("Model and preprocessors are successfully loaded and resident in memory!")

dummy_image = Image.new("RGB", (224, 224), color=(0, 0, 0))
vision_inputs = vision_processor(images=[dummy_image], return_tensors="pt")
pixel_values = vision_inputs["pixel_values"]

def predict_batch(entries):
    results = []

    for entry in entries:
        audio_path = entry.audioPath

        if not os.path.exists(audio_path):
            print(f"Warning: File not found at '{audio_path}'")
            results.append({
                "fromMs": entry.fromMs,
                "toMs": entry.toMs,
                "speaker": entry.speaker,
                "audioPath": entry.audioPath,
                "text": entry.text,
                "emotionPrediction": "File Not Found",
                "confidence": 0.0,
                "words": entry.words
            })
            continue

        try:
            text_inputs = text_tokenizer(
                entry.text, 
                padding="max_length", 
                truncation=True,
                max_length=128, 
                return_tensors="pt"
            )

            audio, _ = librosa.load(audio_path, sr=16000)
            target_length = 3 * 16000
            audio = audio[:target_length] if len(audio) > target_length else \
                np.pad(audio, (0, target_length - len(audio)), mode="constant")
            
            audio_inputs = audio_extractor(
                audio, 
                sampling_rate=16000,
                return_tensors="pt", 
                padding=True
            )

            with torch.no_grad():
                outputs = model(
                    input_ids=text_inputs["input_ids"],
                    attention_mask=text_inputs["attention_mask"],
                    audio_values=audio_inputs["input_values"],
                    audio_attention_mask=torch.ones_like(audio_inputs["input_values"]),
                    pixel_values=pixel_values,
                )

            logits = outputs["logits"]
            probs = torch.softmax(logits, dim=-1)
            predicted_id = torch.argmax(logits, dim=-1).item()

            emotion = ID_TO_LABEL[predicted_id]
            confidence = float(probs[0][predicted_id].item())

            results.append({
                "fromMs": entry.fromMs,
                "toMs": entry.toMs,
                "speaker": entry.speaker,
                "audioPath": entry.audioPath,
                "text": entry.text,
                "emotionPrediction": emotion,
                "confidence": confidence,
                "words": entry.words
            })
        except Exception as e:
            print(f"Error processing entry '{audio_path}': {str(e)}")
            results.append({
                "fromMs": entry.fromMs,
                "toMs": entry.toMs,
                "speaker": entry.speaker,
                "audioPath": entry.audioPath,
                "text": entry.text,
                "emotionPrediction": "Error",
                "confidence": 0.0,
                "words": entry.words
            })

    return results