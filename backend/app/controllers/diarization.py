import os
import logging
from fastapi import APIRouter, File, HTTPException, UploadFile
from app.models.diarization import DiarizationResponse
from app.services.diarization import diarization_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/diarization", tags=["Diarization"])

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}


@router.post("/analyze", response_model=DiarizationResponse)
async def analyze_audio(file: UploadFile = File(...)):
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
        logger.info(f"Processing audio file: {file.filename or 'unnamed'}")
        response = await diarization_service.process_audio(
            file_bytes=content, file_extension=ext or ".wav"
        )
        return response
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"An error occurred during processing: {str(e)}"
        )