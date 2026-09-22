import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import FileResponse

from app.models.segment_record import (
    ParquetExportRequest,
    ParquetAppendRequest,
    HFUploadRequest,
    HFDownloadRequest
)
from app.services.parquet_service import ParquetService
from app.services.huggingface_service import HuggingFaceService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/parquet",
    tags=["Parquet & HuggingFace Datasets"]
)


def get_parquet_service() -> ParquetService:
    return ParquetService()


def get_hf_service() -> HuggingFaceService:
    return HuggingFaceService()


@router.post("/export", response_class=FileResponse)
async def export_parquet_file(
    request: ParquetExportRequest,
    background_tasks: BackgroundTasks,
    service: ParquetService = Depends(get_parquet_service)
):
    """
    Generates a temporary Parquet file from a list of records and returns it as a downloadable file.
    """
    try:
        file_path, cleanup_fn = service.create_parquet(
            records=request.records, 
            dataset_name=request.dataset_name
        )
        background_tasks.add_task(cleanup_fn)

        filename = Path(file_path).name
        return FileResponse(
            path=file_path,
            media_type="application/octet-stream",
            filename=filename
        )
    except Exception as e:
        logger.error(f"Failed to export Parquet file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/append")
async def append_to_parquet_dataset(
    request: ParquetAppendRequest,
    service: ParquetService = Depends(get_parquet_service)
):
    """
    Appends new segment records to an existing local Parquet dataset (or creates it if missing).
    """
    try:
        file_path = service.append_to_parquet(
            dataset_name=request.dataset_name, 
            records=request.records
        )
        return {
            "status": "success",
            "message": f"Successfully appended {len(request.records)} records.",
            "file_path": file_path
        }
    except Exception as e:
        logger.error(f"Failed to append to dataset: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_local_parquet_files(
    service: ParquetService = Depends(get_parquet_service)
):
    """
    Lists all locally available Parquet datasets with record counts and file metrics.
    """
    try:
        files = service.list_parquet_files()
        return {"datasets": files}
    except Exception as e:
        logger.error(f"Failed to list dataset files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/slice")
async def get_parquet_elements_slice(
    dataset_name: str = Query(..., description="Target dataset name"),
    offset: int = Query(0, ge=0, description="Start record index (x)"),
    limit: int = Query(10, gt=0, description="Number of elements to fetch (y)"),
    service: ParquetService = Depends(get_parquet_service)
):
    """
    Retrieves a slice of records from index offset (x) to offset + limit (x + y).
    """
    try:
        return service.get_elements_slice(
            dataset_name=dataset_name, 
            offset=offset, 
            limit=limit
        )
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except Exception as e:
        logger.error(f"Failed to fetch dataset slice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# --------------------------------------------------------------------------
# Hugging Face Integration
# --------------------------------------------------------------------------

@router.post("/hf/upload")
async def upload_dataset_to_huggingface(
    request: HFUploadRequest,
    parquet_service: ParquetService = Depends(get_parquet_service),
    hf_service: HuggingFaceService = Depends(get_hf_service)
):
    """
    Uploads or updates a local Parquet dataset directly to a Hugging Face Dataset repository.
    """
    try:
        target_path = parquet_service._resolve_file_path(request.dataset_name)
        if not target_path.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"Local dataset '{request.dataset_name}' not found."
            )

        file_url = hf_service.upload_dataset_file(
            file_path=str(target_path),
            repo_id=request.repo_id,
            token=request.token,
            private=request.private,
            path_in_repo=request.path_in_repo
        )

        return {
            "status": "success",
            "message": "Dataset uploaded/updated successfully on Hugging Face Hub.",
            "url": file_url
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed HF upload process: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hf/download")
async def download_dataset_from_huggingface(
    request: HFDownloadRequest,
    hf_service: HuggingFaceService = Depends(get_hf_service)
):
    """
    Downloads a specific Parquet dataset file from Hugging Face Hub to local storage.
    """
    try:
        downloaded_path = hf_service.download_dataset_file(
            repo_id=request.repo_id,
            filename=request.filename,
            token=request.token
        )

        return {
            "status": "success",
            "message": "Dataset downloaded successfully from Hugging Face.",
            "local_path": downloaded_path
        }
    except Exception as e:
        logger.error(f"Failed HF download process: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))