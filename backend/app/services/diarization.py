import asyncio
import json
import logging
import os
import subprocess
import tempfile
from enum import Enum
from typing import Dict, Optional
from uuid import uuid4
from pydantic import BaseModel

from app.models.diarization import DiarizationResponse

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CRISPASR_BIN = (
    os.path.join(BASE_DIR, "../CrispASR/build/bin/crispasr")
    if not os.path.exists(os.path.join(BASE_DIR, "CrispASR"))
    else os.path.join(BASE_DIR, "CrispASR/build/bin/crispasr")
)
MODEL_PATH = os.path.join(BASE_DIR, "models/moss-transcribe-diarize-0.9b-f16.gguf")


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
        self._errors: Dict[str, str] = {}
        self._processes: Dict[str, subprocess.Popen] = {}

    def get_bin_path(self) -> str:
        if os.path.exists(CRISPASR_BIN):
            return CRISPASR_BIN
        alt_bin = os.path.abspath(
            os.path.join(BASE_DIR, "..", "CrispASR/build/bin/crispasr")
        )
        if os.path.exists(alt_bin):
            return alt_bin
        raise RuntimeError(f"CrispASR binary not found: {CRISPASR_BIN}")

    def start_task(
        self, file_bytes: bytes, file_extension: str, language: Optional[str] = None
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
        language: Optional[str] = None,
    ):
        suffix = file_extension if file_extension.startswith(".") else f".{file_extension}"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_audio_path = os.path.join(temp_dir, f"audio_{task_id}{suffix}")
            output_json_prefix = os.path.join(temp_dir, f"result_{task_id}")
            expected_json_path = f"{output_json_prefix}.json"

            with open(temp_audio_path, "wb") as f:
                f.write(file_bytes)

            cmd = [
                bin_path,
                "--backend",
                "moss-diarize",
                "-m",
                MODEL_PATH,
                "-f",
                temp_audio_path,
                "--output-json-full",
                "-of",
                output_json_prefix,
            ]

            # Ha van language megadva, hozzáadjuk a parancshoz
            if language:
                cmd.extend(["-l", language])

            logger.info(f"Task {task_id}: Starting execution with CLI: {' '.join(cmd)}")
            self._tasks[task_id] = TaskStatus.RUNNING

            try:
                process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                self._processes[task_id] = process

                stdout, stderr = await asyncio.to_thread(process.communicate)

                if process.returncode != 0:
                    if self._tasks[task_id] == TaskStatus.STOPPED:
                        logger.info(
                            f"Task {task_id}: Process execution stopped by user request."
                        )
                        return
                    logger.error(f"Task {task_id}: Process failed with error: {stderr}")
                    self._tasks[task_id] = TaskStatus.FAILED
                    self._errors[task_id] = f"CLI Execution error: {stderr}"
                    return

                if not os.path.exists(expected_json_path):
                    err_msg = f"Output JSON file missing at {expected_json_path}"
                    logger.error(f"Task {task_id}: {err_msg}")
                    self._tasks[task_id] = TaskStatus.FAILED
                    self._errors[task_id] = err_msg
                    return

                with open(expected_json_path, "r", encoding="utf-8") as json_file:
                    raw_data = json.load(json_file)

                response = DiarizationResponse.model_validate(raw_data)

                self._results[task_id] = response
                self._tasks[task_id] = TaskStatus.COMPLETED
                logger.info(f"Task {task_id}: Completed successfully.")

            except Exception as e:
                logger.error(
                    f"Task {task_id}: Exception during execution: {str(e)}",
                    exc_info=True,
                )
                self._tasks[task_id] = TaskStatus.FAILED
                self._errors[task_id] = str(e)
            finally:
                self._processes.pop(task_id, None)

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

    async def process_audio(
        self, file_bytes: bytes, file_extension: str, language: Optional[str] = None
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