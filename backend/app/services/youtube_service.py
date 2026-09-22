import os
import uuid
import logging
import asyncio
import yt_dlp
from typing import Tuple, Callable
from pathlib import Path

logger = logging.getLogger(__name__)

class YouTubeAudioService:
    def __init__(self, temp_dir: str = "/tmp/yt_downloads"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def _download_sync(self, url: str) -> Tuple[str, str]:
        unique_id = uuid.uuid4().hex
        outtmpl = str(self.temp_dir / f'{unique_id}_%(title)s.%(ext)s')

        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'outtmpl': outtmpl,
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'audio_file')
            downloaded_file = ydl.prepare_filename(info)
            wav_file_path = os.path.splitext(downloaded_file)[0] + ".wav"
            
        return wav_file_path, title

    async def download_as_wav(self, clean_url: str) -> Tuple[str, str, Callable[[], None]]:
        logger.info(f"Processing download for sanitized URL: {clean_url}")
        
        try:
            wav_file_path, title = await asyncio.to_thread(self._download_sync, clean_url)
            
            def cleanup():
                try:
                    if os.path.exists(wav_file_path):
                        os.remove(wav_file_path)
                        logger.info(f"Temporary file removed successfully: {wav_file_path}")
                except Exception as e:
                    logger.error(f"Failed to remove temporary file '{wav_file_path}': {e}")

            return wav_file_path, title, cleanup
            
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"yt-dlp download failed for URL '{clean_url}': {str(e)}")
            raise ValueError("The video is unavailable, restricted, or does not exist.")
        except Exception as e:
            logger.error(f"Unexpected error during download: {str(e)}")
            raise