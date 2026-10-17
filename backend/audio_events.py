import csv
import os
import librosa
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub

print("Loading Google YAMNet model from TF Hub...")
yamnet_model = hub.load("https://www.kaggle.com/models/google/yamnet/tensorFlow2/yamnet/1?tfhub-redirect=true")
class_map_path = yamnet_model.class_map_path().numpy().decode("utf-8")
yamnet_classes = []
with open(class_map_path, mode="r") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        yamnet_classes.append(row[2])
print("YAMNet loaded successfully!")

AUDIO_BASE_DIR = "/home/fablevi/.audiotodataset/yt_downloads/"
TARGET_EVENTS = {
    "Cough": "cough",
    "Throat clearing": "clears throat",
    "Laughter": "laughter",
    "Sneeze": "sneeze",
    "Whispering": "whisper",
}
CONFIDENCE_THRESHOLD = 0.35

def detect_events_with_yamnet(audio_path: str):
    if not os.path.exists(audio_path):
        full_path = os.path.join(AUDIO_BASE_DIR, audio_path)
        if os.path.exists(full_path):
            audio_path = full_path
        else:
            return []

    try:
        waveform, sr = librosa.load(audio_path, sr=16000)
    except Exception as e:
        print(f"Error loading audio file ({audio_path}): {e}")
        return []

    scores, embeddings, spectrogram = yamnet_model(waveform)
    scores_np = scores.numpy()

    detected_events = []
    hop_duration_ms = 480

    for frame_idx, frame_scores in enumerate(scores_np):
        frame_start_ms = int(frame_idx * hop_duration_ms)
        frame_end_ms = frame_start_ms + 960

        for target_name, tag_name in TARGET_EVENTS.items():
            try:
                class_idx = yamnet_classes.index(target_name)
                score = frame_scores[class_idx]
                if score >= CONFIDENCE_THRESHOLD:
                    detected_events.append({
                        "type": tag_name,
                        "from": frame_start_ms,
                        "to": frame_end_ms,
                        "score": float(score)
                    })
            except ValueError:
                continue

    filtered_events = []
    for ev in detected_events:
        if not filtered_events or (ev["from"] - filtered_events[-1]["from"] > 800):
            filtered_events.append(ev)

    return filtered_events

def insert_events_into_words(chunk_data: dict, detected_events: list):
    words = chunk_data.get("words", [])
    if not words:
        return chunk_data

    sorted_events = sorted(detected_events, key=lambda x: x["from"])
    new_words = []
    event_idx = 0

    for word in words:
        word_start = word.get("offsets", {}).get("from", 0)

        while event_idx < len(sorted_events):
            ev = sorted_events[event_idx]
            ev_mid = (ev["from"] + ev["to"]) / 2

            if ev_mid < word_start:
                tag_text = f" [{ev['type']}]"
                new_words.append({
                    "text": tag_text,
                    "t0": 0,
                    "t1": 0,
                    "offsets": {"from": ev["from"], "to": ev["to"]}
                })
                event_idx += 1
            else:
                break

        new_words.append(word)

    while event_idx < len(sorted_events):
        ev = sorted_events[event_idx]
        tag_text = f" [{ev['type']}]"
        new_words.append({
            "text": tag_text,
            "t0": 0,
            "t1": 0,
            "offsets": {"from": ev["from"], "to": ev["to"]}
        })
        event_idx += 1

    chunk_data["words"] = new_words
    chunk_data["text"] = "".join([w.get("text", "") for w in new_words])
    return chunk_data

def detect_batch(entries: list) -> list:
    processed_results = []
    for entry in entries:
        entry_dict = entry.dict() if hasattr(entry, "dict") else dict(entry)
        audio_path = entry_dict.get("audioPath")

        if audio_path:
            events = detect_events_with_yamnet(audio_path)
            if events:
                entry_dict = insert_events_into_words(entry_dict, events)

        processed_results.append(entry_dict)
    return processed_results