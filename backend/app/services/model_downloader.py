import logging
import os
import shutil
import urllib.request

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STORAGE_DIR = os.path.join(BASE_DIR, "storage", "audio")

MODEL_PATH = os.path.join(BASE_DIR, "models/ggml-large-v3-turbo.bin")
EMBEDDER_PATH = os.path.join(BASE_DIR, "models/wespeaker-resnet34-lm-f32.gguf")

WHISPER_MODEL_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin?download=true"
EMBEDDER_MODEL_URL = "https://huggingface.co/cstr/wespeaker-resnet34-lm-GGUF/resolve/main/wespeaker-resnet34-lm-f32.gguf?download=true"


class ModelInitializerService:

    @staticmethod
    def clean_storage():
        """Cleans up the storage/audio directory before every application startup."""
        if os.path.exists(STORAGE_DIR):
            try:
                shutil.rmtree(STORAGE_DIR)
                logger.info(f"Cleaned existing storage directory: {STORAGE_DIR}")
            except Exception as e:
                logger.error(f"Error cleaning storage directory: {e}")
        os.makedirs(STORAGE_DIR, exist_ok=True)

    @classmethod
    def ensure_models_exist(cls):
        """Checks for required model files and downloads them if missing."""
        models_dir = os.path.dirname(MODEL_PATH)
        os.makedirs(models_dir, exist_ok=True)

        cls._download_file_if_missing(MODEL_PATH, WHISPER_MODEL_URL)
        cls._download_file_if_missing(EMBEDDER_PATH, EMBEDDER_MODEL_URL)

    @staticmethod
    def _download_file_if_missing(file_path: str, url: str):
        if not os.path.exists(file_path):
            filename = os.path.basename(file_path)
            logger.info(f"Model missing: {filename}. Starting download from HuggingFace...")
            try:
                def progress(count, block_size, total_size):
                    percent = int(count * block_size * 100 / total_size)
                    if percent % 20 == 0:
                        logger.info(f"Downloading {filename}: {percent}%")

                urllib.request.urlretrieve(url, file_path, reporthook=progress)
                logger.info(f"Successfully downloaded model: {filename}")
            except Exception as e:
                logger.error(f"Failed to download model {filename}: {e}")
                if os.path.exists(file_path):
                    os.remove(file_path)
                raise RuntimeError(f"Could not download required model {filename}: {e}")


model_initializer_service = ModelInitializerService()