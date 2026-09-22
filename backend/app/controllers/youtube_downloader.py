import urllib.parse
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse

from app.models.video_dwnload_request import VideoDownloadRequest
from app.services.youtube_service import YouTubeAudioService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/youtube",
    tags=["YouTube Downloader"]
)

def get_youtube_service() -> YouTubeAudioService:
    return YouTubeAudioService()

@router.post("/download-wav", response_class=FileResponse)
async def download_wav(
    request: VideoDownloadRequest, 
    background_tasks: BackgroundTasks,
    service: YouTubeAudioService = Depends(get_youtube_service)
):
    try:
        url_str = str(request.url)
        
        file_path, title, cleanup_fn = await service.download_as_wav(url_str)
        
        background_tasks.add_task(cleanup_fn)
        
        safe_filename = f"{urllib.parse.quote(title)}.wav"

        return FileResponse(
            path=file_path,
            media_type="audio/wav",
            filename=f"{title}.wav",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}"
            }
        )

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to process YouTube audio extraction: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="An internal server error occurred while processing the request."
        )