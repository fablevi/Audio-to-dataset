import logging
import os
import mimetypes
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.controllers.diarization import router as diarization_router
from app.controllers.youtube_downloader import router as youtube_downloader_router 
from app.services.model_downloader import model_initializer_service
from app.controllers.parquet_controller import router as parquet_router

# SVG és statikus MIME típusok biztosítása
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/javascript", ".js")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Initializing application startup tasks...")
    model_initializer_service.clean_storage()
    model_initializer_service.ensure_models_exist()
    yield
    logging.info("Shutting down application...")


app = FastAPI(
    title="CrispASR Diarization REST API",
    version="1.0.0",
    description="ASR and Speaker Diarization API based on CrispASR",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Controller routerek regisztrálása
app.include_router(diarization_router)
app.include_router(youtube_downloader_router)
app.include_router(parquet_router)

# Statikus mappák csatolása a /static és /assets útvonalakhoz
app.mount("/static", StaticFiles(directory="static"), name="static")

if os.path.exists("static/assets"):
    app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.get("/{path:path}")
async def serve_spa(path: str):
    # 1. Ellenőrizzük, hogy a kérvényezett fájl létezik-e a static mappában
    file_path = os.path.join("static", path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # 2. Ha nem létezik fizikai fájlként, akkor SPA útvonal -> fallback az index.html-re
    return FileResponse("static/index.html")


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok"}