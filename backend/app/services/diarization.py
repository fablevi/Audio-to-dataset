import os
import re
import subprocess
import tempfile
import logging
import asyncio
from typing import Dict, Optional
from uuid import uuid4
from enum import Enum
from pydantic import BaseModel
from app.models.diarization import DiarizationResponse, SpeakerTurn

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

    def parse_output(self, raw_output: str) -> DiarizationResponse:
        segments_data = []
        unique_speakers = set()

        logger.debug(f"Parsing raw CLI output:\n{raw_output}")

        # 1. Minta: [0.68] Levanta területén... [2.68] (Beszélővel vagy anélkül)
        pattern_with_end_ts = re.compile(
            r"\[(?P<start>\d+\.\d+)\]\s*(?:\[(?P<speaker>S\d+|SPEAKER_\d+|spk\d+)\]\s*)?(?P<text>.*?)\s*\[(?P<end>\d+\.\d+)\]",
            re.DOTALL | re.IGNORECASE,
        )

        matches = list(pattern_with_end_ts.finditer(raw_output))

        if matches:
            for match in matches:
                spk = match.group("speaker")
                spk = spk.upper() if spk else "SPEAKER_00"
                start_time = float(match.group("start"))
                end_time = float(match.group("end"))
                clean_text = match.group("text").strip()

                if clean_text:
                    # Duplikátum szűrés: ha a legutóbbi szegmens pontosan ugyanaz, kihagyjuk
                    if segments_data:
                        last_seg = segments_data[-1]
                        if (
                            last_seg.speaker == spk
                            and last_seg.start == round(start_time, 2)
                            and last_seg.end == round(end_time, 2)
                            and last_seg.text == clean_text
                        ):
                            continue

                    unique_speakers.add(spk)
                    segments_data.append(
                        SpeakerTurn(
                            speaker=spk,
                            start=round(start_time, 2),
                            end=round(end_time, 2),
                            text=clean_text,
                        )
                    )

        # 2. Minta: Hagyományos szegmentált minta (ha nincs záró időbélyeg)
        if not segments_data:
            strict_pattern = re.compile(
                r"\[(?P<start>\d+\.\d+)\]\s*(?:\[(?P<speaker>S\d+|SPEAKER_\d+|spk\d+)\]\s*)?(?P<text>.*?)(?=\[\d+\.\d+\]|$)",
                re.DOTALL | re.IGNORECASE,
            )
            strict_matches = list(strict_pattern.finditer(raw_output))

            for i, match in enumerate(strict_matches):
                spk = match.group("speaker")
                spk = spk.upper() if spk else "SPEAKER_00"
                start_time = float(match.group("start"))
                raw_text = match.group("text").strip()
                clean_text = re.sub(r"\[\d+\.\d+\]", "", raw_text).strip()

                if not clean_text:
                    continue

                if i + 1 < len(strict_matches):
                    end_time = float(strict_matches[i + 1].group("start"))
                else:
                    end_time = round(start_time + 3.0, 2)

                # Duplikátum szűrés
                if segments_data:
                    last_seg = segments_data[-1]
                    if (
                        last_seg.speaker == spk
                        and last_seg.start == round(start_time, 2)
                        and last_seg.text == clean_text
                    ):
                        continue

                unique_speakers.add(spk)
                segments_data.append(
                    SpeakerTurn(
                        speaker=spk,
                        start=round(start_time, 2),
                        end=round(end_time, 2),
                        text=clean_text,
                    )
                )

        if not segments_data:
            logger.warning(
                f"Failed to parse any segments from raw output. Raw content:\n{raw_output}"
            )

        return DiarizationResponse(
            speaker_count=len(unique_speakers),
            speakers=sorted(list(unique_speakers)),
            segments=segments_data,
        )

    def start_task(
        self, file_bytes: bytes, file_extension: str, language: str = "en"
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
        language: str,
    ):
        suffix = (
            file_extension
            if file_extension.startswith(".")
            else f".{file_extension}"
        )
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_file.write(file_bytes)
        temp_file.close()
        temp_path = temp_file.name

        cmd = [
            bin_path,
            "--backend",
            "moss-diarize",
            "-m",
            MODEL_PATH,
            "-f",
            temp_path,
            "-l",
            language,
        ]

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

            raw_output = (stdout or "") + "\n" + (stderr or "")
            response = self.parse_output(raw_output)

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
            if os.path.exists(temp_path):
                os.remove(temp_path)

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
        self, file_bytes: bytes, file_extension: str, language: str = "en"
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