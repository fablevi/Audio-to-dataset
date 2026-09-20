from typing import List, Optional
from pydantic import BaseModel, Field


class CrispASRMetadata(BaseModel):
    backend: str
    model: str
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
    speaker: str
    text: str
    chunk_id: int


class DiarizationResponse(BaseModel):
    crispasr: CrispASRMetadata
    transcription: List[TranscriptionSegment]