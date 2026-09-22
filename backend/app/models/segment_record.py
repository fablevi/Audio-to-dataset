from pydantic import BaseModel, Field
from typing import List, Optional


class SegmentRecord(BaseModel):
    speaker: str = Field(
        ..., 
        description="Speaker identifier (e.g., SPEAKER_00)"
    )
    start: float = Field(
        ..., 
        description="Start timestamp in seconds (e.g., 12.45)"
    )
    stop: float = Field(
        ..., 
        description="End timestamp in seconds (e.g., 18.20)"
    )
    videolink: str = Field(
        ..., 
        description="Source YouTube video URL"
    )
    language: Optional[str] = Field(
        default=None, 
        description="Language code of the audio segment (e.g., 'hu', 'en')"
    )
    text: Optional[str] = Field(
        default=None, 
        description="Transcribed text corresponding to the segment"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "speaker": "SPEAKER_01",
                "start": 12.5,
                "stop": 18.2,
                "videolink": "https://www.youtube.com/watch?v=97NyFeKGlB8",
                "language": "en",
                "text": "Sample transcribed sentence from the audio."
            }
        }


class ParquetExportRequest(BaseModel):
    dataset_name: str = Field(
        default="dataset", 
        description="Base name for the generated Parquet file (without extension)"
    )
    records: List[SegmentRecord] = Field(
        ..., 
        description="List of segment records to be exported"
    )


class ParquetAppendRequest(BaseModel):
    dataset_name: str = Field(
        ..., 
        description="Target dataset name to update/append records to"
    )
    records: List[SegmentRecord] = Field(
        ..., 
        description="List of new segment records to append"
    )


class HFUploadRequest(BaseModel):
    dataset_name: str = Field(
        ..., 
        description="Name of the local dataset file (e.g. 'my_dataset' or 'my_dataset.parquet')"
    )
    repo_id: str = Field(
        ..., 
        description="Hugging Face repo ID in format 'username/dataset-name'"
    )
    token: Optional[str] = Field(
        default=None, 
        description="Optional Hugging Face Write Token (overrides server default)"
    )
    private: bool = Field(
        default=False, 
        description="Whether the HF repository should be private if created"
    )
    path_in_repo: Optional[str] = Field(
        default=None, 
        description="Target relative path inside the HF repository"
    )


class HFDownloadRequest(BaseModel):
    repo_id: str = Field(
        ..., 
        description="Hugging Face dataset repository ID"
    )
    filename: str = Field(
        ..., 
        description="Filename to download from the repo (e.g., 'data.parquet')"
    )
    token: Optional[str] = Field(
        default=None, 
        description="Optional Hugging Face Read Token for private datasets"
    )