from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from huggingface_hub import HfApi
import os

app = FastAPI()

class UploadRequest(BaseModel):
    local_folder_path: str
    repo_name: str
    hf_token: str
    repo_type: str = "dataset"
    commit_message: str = "Upload via FastAPI"

@app.post("/upload", status_code=status.HTTP_200_OK)
def upload_to_huggingface(payload: UploadRequest):
    if not os.path.exists(payload.local_folder_path) or not os.path.isdir(payload.local_folder_path):
        raise HTTPException(
            status_code=400,
            detail=f"Local folder does not exist: {payload.local_folder_path}"
        )

    try:
        api = HfApi(token=payload.hf_token)

        api.create_repo(
            repo_id=payload.repo_name,
            repo_type=payload.repo_type,
            exist_ok=True
        )

        api.upload_folder(
            folder_path=payload.local_folder_path,
            repo_id=payload.repo_name,
            repo_type=payload.repo_type,
            commit_message=payload.commit_message
        )

        return {
            "status": "success",
            "message": f"Successfully uploaded to {payload.repo_name}",
            "repo_url": f"https://huggingface.co/{'datasets/' if payload.repo_type == 'dataset' else ''}{payload.repo_name}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
