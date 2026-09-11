from pydantic import BaseModel, Field


class SpeakerTurn(BaseModel):
    speaker: str = Field(..., description="Speaker identifier (e.g. SPEAKER_00)")
    start: float = Field(..., description="Segment start time in seconds")
    end: float = Field(..., description="Segment end time in seconds")
    text: str = Field(..., description="Transcribed text segment")


class DiarizationResponse(BaseModel):
    speaker_count: int = Field(..., description="Total number of detected speakers")
    speakers: list[str] = Field(..., description="List of speaker identifiers")
    segments: list[SpeakerTurn] = Field(
        ..., description="Chronological list of speaker turns and transcriptions"
    )