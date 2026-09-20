import asyncio
import json
import logging
import os
import subprocess
from enum import Enum
from typing import Dict, Optional
from uuid import uuid4
from pydantic import BaseModel

from app.models.diarization import DiarizationResponse

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STORAGE_DIR = os.path.join(BASE_DIR, "storage", "audio")

CRISPASR_BIN = os.path.join(BASE_DIR, "CrispASR/build/bin/crispasr")
MODEL_PATH = os.path.join(BASE_DIR, "models/ggml-large-v3-turbo.bin")
EMBEDDER_PATH = os.path.join(BASE_DIR, "models/wespeaker-resnet34-lm-f32.gguf")


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class StatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    is_running: bool
    error: Optional[str] = None


class DiarizationService:

    def __init__(self):
        self._tasks: Dict[str, TaskStatus] = {}
        self._results: Dict[str, DiarizationResponse] = {}
        self._raw_json_results: Dict[str, dict] = {}
        self._errors: Dict[str, str] = {}
        self._processes: Dict[str, subprocess.Popen] = {}
        self._audio_files: Dict[str, str] = {}
        os.makedirs(STORAGE_DIR, exist_ok=True)

    def get_bin_path(self) -> str:
        if os.path.exists(CRISPASR_BIN):
            return CRISPASR_BIN
        alt_bin = os.path.abspath(
            os.path.join(BASE_DIR, "..", "backend/CrispASR/build/bin/crispasr")
        )
        if os.path.exists(alt_bin):
            return alt_bin
        raise RuntimeError(f"CrispASR binary not found: {CRISPASR_BIN}")

    def get_audio_path(self, task_id: str) -> Optional[str]:
        path = self._audio_files.get(task_id)
        if path and os.path.exists(path):
            return path
        return None

    def extract_audio_chunk_bytes(
        self, input_path: str, start_ms: int, end_ms: int
    ) -> Optional[bytes]:
        try:
            start_sec = max(0, start_ms) / 1000.0
            duration_sec = max(0, end_ms - start_ms) / 1000.0

            if duration_sec <= 0:
                logger.warning(
                    f"Invalid duration: start_ms={start_ms}, end_ms={end_ms}"
                )
                return None

            cmd = [
                "ffmpeg",
                "-y",
                "-ss",
                f"{start_sec:.3f}",
                "-i",
                input_path,
                "-t",
                f"{duration_sec:.3f}",
                "-c:a",
                "pcm_s16le",
                "-ar",
                "16000",
                "-ac",
                "1",
                "-f",
                "wav",
                "-loglevel",
                "quiet",
                "pipe:1",
            ]

            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            out, err = process.communicate()

            if process.returncode == 0 and out:
                return out
            else:
                err_msg = err.decode("utf-8", errors="replace") if err else "Unknown"
                logger.error(
                    f"FFmpeg error (code {process.returncode}): {err_msg}"
                )
        except Exception as e:
            logger.warning(
                f"FFmpeg slicing failed for {start_ms}-{end_ms} ms: {e}"
            )

        return None

    def start_task(
        self, file_bytes: bytes, file_extension: str, language: Optional[str] = "hu"
    ) -> str:
        bin_to_use = self.get_bin_path()

        if not os.path.exists(MODEL_PATH):
            raise RuntimeError(f"Model file not found at path: {MODEL_PATH}")

        task_id = str(uuid4())
        self._tasks[task_id] = TaskStatus.PENDING

        asyncio.create_task(
            self._run_async_process(
                task_id, bin_to_use, file_bytes, file_extension, language
            )
        )
        return task_id

    async def _run_async_process(
        self,
        task_id: str,
        bin_path: str,
        file_bytes: bytes,
        file_extension: str,
        language: Optional[str] = "hu",
    ):
        suffix = (
            file_extension if file_extension.startswith(".") else f".{file_extension}"
        )

        raw_audio_path = os.path.join(STORAGE_DIR, f"{task_id}_raw{suffix}")
        audio_file_path = os.path.join(STORAGE_DIR, f"{task_id}.wav")
        output_json_prefix = os.path.join(STORAGE_DIR, f"result_{task_id}")
        expected_json_path = f"{output_json_prefix}.json"

        try:
            with open(raw_audio_path, "wb") as f:
                f.write(file_bytes)

            convert_cmd = [
                "ffmpeg",
                "-y",
                "-i",
                raw_audio_path,
                "-ar",
                "16000",
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                "-loglevel",
                "quiet",
                audio_file_path,
            ]
            await asyncio.to_thread(subprocess.run, convert_cmd, check=True)

            if os.path.exists(raw_audio_path):
                os.remove(raw_audio_path)

            self._audio_files[task_id] = audio_file_path

            cmd = [
                bin_path,
                "--backend",
                "whisper",
                "-m",
                MODEL_PATH,
                "-f",
                audio_file_path,
                "--output-json-full",
                "-of",
                output_json_prefix,
                "--diarize",
                "--diarize-method",
                "foxnose",
                "--vad",
            ]

            if language:
                cmd.extend(["-l", language])
                
            if os.path.exists(EMBEDDER_PATH):
                cmd.extend(["--diarize-embedder", EMBEDDER_PATH])

            logger.info(
                f"Task {task_id}: Starting execution with CLI: {' '.join(cmd)}"
            )
            self._tasks[task_id] = TaskStatus.RUNNING

            # Megjegyzés: Nincs text=True, nyers byte-okkal dolgozunk a decode hiba elkerülésére!
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self._processes[task_id] = process

            stdout_bytes, stderr_bytes = await asyncio.to_thread(process.communicate)

            stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""

            if process.returncode != 0:
                if self._tasks[task_id] == TaskStatus.STOPPED:
                    logger.info(
                        f"Task {task_id}: Process execution stopped by user request."
                    )
                    return
                logger.error(
                    f"Task {task_id}: Process failed with error: {stderr}"
                )
                self._tasks[task_id] = TaskStatus.FAILED
                self._errors[task_id] = f"CLI Execution error: {stderr}"
                return

            if not os.path.exists(expected_json_path):
                err_msg = f"Output JSON file missing at {expected_json_path}"
                logger.error(f"Task {task_id}: {err_msg}")
                self._tasks[task_id] = TaskStatus.FAILED
                self._errors[task_id] = err_msg
                return

            with open(expected_json_path, "r", encoding="utf-8", errors="replace") as json_file:
                raw_data = json.load(json_file)

            transcription_list = raw_data.get("transcription", [])

            for idx, segment in enumerate(transcription_list):
                segment["chunk_id"] = idx

                speaker = segment.get("speaker", "").strip()
                if not speaker:
                    segment["speaker"] = "Speaker 0"
                else:
                    cleaned_speaker = speaker.replace("(", "").replace(")", "").strip().title()
                    segment["speaker"] = cleaned_speaker

                segment["speech"] = f"/api/v1/diarization/audio/{task_id}/{idx}"

            self._raw_json_results[task_id] = raw_data
            response = DiarizationResponse.model_validate(raw_data)

            self._results[task_id] = response
            self._tasks[task_id] = TaskStatus.COMPLETED
            logger.info(
                f"Task {task_id}: Completed successfully with {len(transcription_list)} segments."
            )

        except Exception as e:
            logger.error(
                f"Task {task_id}: Exception during execution: {str(e)}",
                exc_info=True,
            )
            self._tasks[task_id] = TaskStatus.FAILED
            self._errors[task_id] = str(e)
        finally:
            self._processes.pop(task_id, None)
            if os.path.exists(expected_json_path):
                try:
                    os.remove(expected_json_path)
                except Exception:
                    pass

    def stop_task(self, task_id: str) -> bool:
        if task_id not in self._tasks:
            return False

        process = self._processes.get(task_id)
        if process:
            logger.info(f"Task {task_id}: Terminating active CLI process.")
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
            self._processes.pop(task_id, None)

        self._tasks[task_id] = TaskStatus.STOPPED
        return True

    def get_task_status(self, task_id: str) -> Optional[StatusResponse]:
        status = self._tasks.get(task_id)
        if not status:
            return None

        is_running = status in (TaskStatus.PENDING, TaskStatus.RUNNING)
        error_msg = self._errors.get(task_id)
        return StatusResponse(
            task_id=task_id, status=status, is_running=is_running, error=error_msg
        )

    def get_task_data(self, task_id: str) -> Optional[DiarizationResponse]:
        return self._results.get(task_id)

    def get_raw_data(self, task_id: str) -> Optional[dict]:
        return self._raw_json_results.get(task_id)

    async def process_audio(
        self, file_bytes: bytes, file_extension: str, language: Optional[str] = "hu"
    ) -> DiarizationResponse:
        task_id = self.start_task(file_bytes, file_extension, language)
        while True:
            info = self.get_task_status(task_id)
            if info.status == TaskStatus.COMPLETED:
                return self.get_task_data(task_id)
            if info.status in (TaskStatus.FAILED, TaskStatus.STOPPED):
                raise RuntimeError(info.error or "Process stopped or failed.")
            await asyncio.sleep(0.2)


diarization_service = DiarizationService()