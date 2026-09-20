import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers.diarization import router as diarization_router
from app.services.model_downloader import model_initializer_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs on application startup:
    logging.info("Initializing application startup tasks...")
    model_initializer_service.clean_storage()
    model_initializer_service.ensure_models_exist()
    yield
    # Runs on application shutdown:
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

# Register controllers
app.include_router(diarization_router)


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok"}