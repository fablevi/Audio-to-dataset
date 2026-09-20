from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CrispASRMetadata(BaseModel):
    backend: Optional[str] = "whisper"
    model: Optional[str] = None
    language: Optional[str] = None


class TimestampRange(BaseModel):
    from_: Optional[str] = Field(default=None, alias="from")
    to: str

    class Config:
        populate_by_name = True


class OffsetRange(BaseModel):
    from_: Optional[int] = Field(default=None, alias="from")
    to: int

    class Config:
        populate_by_name = True


class TranscriptionSegment(BaseModel):
    timestamps: TimestampRange
    offsets: OffsetRange
    speaker: Optional[str] = "Speaker 0"
    text: Optional[str] = ""
    chunk_id: Optional[int] = 0
    speech: Optional[str] = None
    words: Optional[List[Dict[str, Any]]] = None
    tokens: Optional[List[Dict[str, Any]]] = None

    class Config:
        extra = "ignore"


class DiarizationResponse(BaseModel):
    crispasr: Optional[CrispASRMetadata] = None
    transcription: List[TranscriptionSegment] = []

    class Config:
        extra = "ignore"