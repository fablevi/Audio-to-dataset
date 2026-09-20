import logging
import os
from typing import Optional
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.diarization import DiarizationResponse
from app.services.diarization import StatusResponse, diarization_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/diarization", tags=["Diarization"])

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}


@router.post("/start")
async def start_diarization(
    file: UploadFile = File(...), language: Optional[str] = None
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


@router.post("/analyze", response_model=DiarizationResponse)
async def analyze_audio(
    file: UploadFile = File(...), language: Optional[str] = None
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