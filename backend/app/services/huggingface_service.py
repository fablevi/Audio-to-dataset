import os
import logging
from pathlib import Path
from typing import Optional
from huggingface_hub import HfApi, hf_hub_download, snapshot_download

logger = logging.getLogger(__name__)


class HuggingFaceService:
    def __init__(
        self, 
        default_token: Optional[str] = None, 
        default_download_dir: str = "/tmp/hf_downloads"
    ):
        self.default_token = (
            default_token 
            or os.getenv("HF_TOKEN") 
            or os.getenv("HUGGING_FACE_HUB_TOKEN")
        )
        self.download_dir = Path(default_download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_token(self, token: Optional[str] = None) -> Optional[str]:
        """
        Resolves the Hugging Face token from explicit call argument or service default.
        """
        resolved = token or self.default_token
        if not resolved:
            logger.warning("No Hugging Face token provided. Operations on private repositories will fail.")
        return resolved

    def upload_dataset_file(
        self,
        file_path: str,
        repo_id: str,
        token: Optional[str] = None,
        private: bool = False,
        path_in_repo: Optional[str] = None
    ) -> str:
        """
        Uploads a single local file (e.g., a .parquet file) to a Hugging Face Dataset repository.
        Creates the dataset repository if it does not already exist.

        :param file_path: Path to the local file to upload.
        :param repo_id: Hugging Face repo ID in format 'username/dataset_name'.
        :param token: Optional HF API Token (overrides default/env token).
        :param private: Whether the repository should be private if newly created.
        :param path_in_repo: Target path/filename inside the HF repo (defaults to local filename).
        :return: Public URL of the uploaded file on Hugging Face Hub.
        """
        resolved_token = self._resolve_token(token)
        if not resolved_token:
            raise ValueError("Hugging Face API token is required to upload datasets.")

        local_file = Path(file_path)
        if not local_file.exists():
            raise FileNotFoundError(f"Local file to upload does not exist: {file_path}")

        target_path_in_repo = path_in_repo or local_file.name

        try:
            api = HfApi(token=resolved_token)
            
            # Ensure the dataset repository exists
            api.create_repo(
                repo_id=repo_id,
                repo_type="dataset",
                private=private,
                exist_ok=True
            )

            logger.info(f"Uploading file '{local_file.name}' to HF dataset repo '{repo_id}'...")
            
            file_url = api.upload_file(
                path_or_fileobj=str(local_file),
                path_in_repo=target_path_in_repo,
                repo_id=repo_id,
                repo_type="dataset"
            )

            logger.info(f"Successfully uploaded file to Hugging Face: {file_url}")
            return file_url

        except Exception as e:
            logger.error(f"Failed to upload file '{file_path}' to HF dataset repo '{repo_id}': {str(e)}")
            raise

    def download_dataset_file(
        self,
        repo_id: str,
        filename: str,
        token: Optional[str] = None,
        target_dir: Optional[str] = None
    ) -> str:
        """
        Downloads a specific file (e.g. 'data.parquet') from a Hugging Face Dataset repository.

        :param repo_id: Hugging Face repo ID (e.g., 'org/dataset-name').
        :param filename: Filename within the repo to download.
        :param token: Optional HF API Token.
        :param target_dir: Optional custom local directory for saving the file.
        :return: Absolute local file path of the downloaded file.
        """
        resolved_token = self._resolve_token(token)
        destination_dir = Path(target_dir) if target_dir else self.download_dir
        destination_dir.mkdir(parents=True, exist_ok=True)

        try:
            logger.info(f"Downloading '{filename}' from HF dataset repo '{repo_id}'...")
            
            downloaded_file_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                repo_type="dataset",
                token=resolved_token,
                local_dir=str(destination_dir)
            )

            logger.info(f"File downloaded successfully to: {downloaded_file_path}")
            return downloaded_file_path

        except Exception as e:
            logger.error(f"Failed to download file '{filename}' from HF repo '{repo_id}': {str(e)}")
            raise

    def download_full_dataset_repo(
        self,
        repo_id: str,
        token: Optional[str] = None,
        target_dir: Optional[str] = None
    ) -> str:
        """
        Downloads all files in a Hugging Face Dataset repository locally.

        :param repo_id: Hugging Face repo ID (e.g., 'org/dataset-name').
        :param token: Optional HF API Token.
        :param target_dir: Optional custom local directory to store the dataset repository.
        :return: Absolute local folder path of the downloaded repository snapshot.
        """
        resolved_token = self._resolve_token(token)
        safe_folder_name = repo_id.replace("/", "_")
        destination_dir = Path(target_dir) if target_dir else (self.download_dir / safe_folder_name)
        destination_dir.mkdir(parents=True, exist_ok=True)

        try:
            logger.info(f"Downloading snapshot for entire dataset repo '{repo_id}'...")
            
            snapshot_path = snapshot_download(
                repo_id=repo_id,
                repo_type="dataset",
                token=resolved_token,
                local_dir=str(destination_dir)
            )

            logger.info(f"Dataset repository downloaded successfully to: {snapshot_path}")
            return snapshot_path

        except Exception as e:
            logger.error(f"Failed to download snapshot for HF dataset repo '{repo_id}': {str(e)}")
            raise