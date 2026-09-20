import logging
import os
from typing import Optional
from fastapi import APIRouter, File, HTTPException, Response, UploadFile

from app.models.diarization import DiarizationResponse
from app.services.diarization import StatusResponse, diarization_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/diarization", tags=["Diarization"])

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}


@router.post("/start")
async def start_diarization(
    file: UploadFile = File(...), language: Optional[str] = "hu"
):
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
    is_valid_mime = file.content_type and file.content_type.startswith("audio/")
    is_valid_ext = ext in ALLOWED_EXTENSIONS

    if not (is_valid_mime or is_valid_ext):
        logger.warning(
            f"Invalid upload attempt: filename={file.filename}, content_type={file.content_type}"
        )
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a valid audio file.",
        )

    content = await file.read()
    try:
        logger.info(
            f"Starting background task for audio file: {file.filename or 'unnamed'}"
        )
        task_id = diarization_service.start_task(
            file_bytes=content, file_extension=ext or ".mp3", language=language
        )
        return {"task_id": task_id, "status": "started"}
    except Exception as e:
        logger.error(f"Error starting task: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop/{task_id}")
async def stop_diarization(task_id: str):
    success = diarization_service.stop_task(task_id)
    if not success:
        raise HTTPException(
            status_code=404, detail="Task not found or already completed."
        )
    return {"task_id": task_id, "status": "stopped"}


@router.get("/status/{task_id}", response_model=StatusResponse)
async def get_task_status(task_id: str):
    info = diarization_service.get_task_status(task_id)
    if not info:
        raise HTTPException(status_code=404, detail="Task not found.")
    return info


@router.get("/getdata/{task_id}", response_model=DiarizationResponse)
async def get_task_data(task_id: str):
    info = diarization_service.get_task_status(task_id)
    if not info:
        raise HTTPException(status_code=404, detail="Task not found.")

    if info.is_running:
        raise HTTPException(
            status_code=400, detail="Task is still running. Please try again later."
        )

    data = diarization_service.get_task_data(task_id)
    if not data:
        raise HTTPException(
            status_code=404,
            detail="No data available for this task (task might have failed or stopped).",
        )

    return data


@router.get("/audio/{task_id}/{chunk_id}")
async def get_audio_chunk(task_id: str, chunk_id: int):
    """Visszaadja a megadott feladat adott szegmensének hanganyagát WAV-ként."""
    raw_data = diarization_service.get_raw_data(task_id)
    if not raw_data:
        raise HTTPException(status_code=404, detail="Task or data not found.")

    transcription = raw_data.get("transcription", [])

    if chunk_id < 0 or chunk_id >= len(transcription):
        raise HTTPException(
            status_code=404,
            detail=f"Chunk ID {chunk_id} out of bounds (total segments: {len(transcription)}).",
        )

    target_segment = transcription[chunk_id]

    audio_path = diarization_service.get_audio_path(task_id)
    if not audio_path or not os.path.exists(audio_path):
        raise HTTPException(
            status_code=404, detail="Original audio file not found on disk."
        )

    offsets = target_segment.get("offsets", {})

    start_ms = offsets.get("from")
    end_ms = offsets.get("to")

    if start_ms is None or end_ms is None:
        raise HTTPException(
            status_code=400, detail=f"Invalid offset timestamps in segment: {offsets}"
        )

    # Vágási pontosság javítása: kis biztonsági margó (50ms)
    PADDING_MS = 50
    start_ms = max(0, int(start_ms) - PADDING_MS)
    end_ms = int(end_ms) + PADDING_MS

    chunk_bytes = diarization_service.extract_audio_chunk_bytes(
        audio_path, start_ms, end_ms
    )
    if not chunk_bytes:
        raise HTTPException(
            status_code=500, detail="Failed to extract audio segment."
        )

    return Response(content=chunk_bytes, media_type="audio/wav")


@router.post("/analyze", response_model=DiarizationResponse)
async def analyze_audio(
    file: UploadFile = File(...), language: Optional[str] = "hu"
):
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
    is_valid_mime = file.content_type and file.content_type.startswith("audio/")
    is_valid_ext = ext in ALLOWED_EXTENSIONS

    if not (is_valid_mime or is_valid_ext):
        logger.warning(
            f"Invalid upload attempt: filename={file.filename}, content_type={file.content_type}"
        )
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a valid audio file.",
        )

    content = await file.read()

    try:
        logger.info(
            f"Synchronous processing started for audio file: {file.filename or 'unnamed'}"
        )
        response = await diarization_service.process_audio(
            file_bytes=content, file_extension=ext or ".mp3", language=language
        )
        return response
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"An error occurred during processing: {str(e)}"
        )