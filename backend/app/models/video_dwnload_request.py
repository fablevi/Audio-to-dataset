import re
from pydantic import BaseModel, field_validator

class VideoDownloadRequest(BaseModel):
    url: str

    @field_validator('url')
    @classmethod
    def clean_and_extract_youtube_url(cls, v: str) -> str:
        url_str = str(v).strip()
        
        youtube_regex = r'(?:youtube\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?|shorts)/|.*[?&]v=)|youtu\.be/)([^"&?/\s]{11})'
        
        match = re.search(youtube_regex, url_str)
        if not match:
            raise ValueError("Invalid YouTube URL or video ID could not be extracted.")
        
        video_id = match.group(1)
        
        clean_url = f"https://www.youtube.com/watch?v={video_id}"
        return clean_url

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.youtube.com/watch?v=97NyFeKGlB8&list=RD97NyFeKGlB8"
            }
        }