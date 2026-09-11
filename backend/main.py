from fastapi import FastAPI
from app.controllers.diarization import router as diarization_router

app = FastAPI(
    title="CrispASR Diarization REST API",
    version="1.0.0",
    description="ASR és Speaker Diarization API CrispASR alapon",
)

# Controller-ek regisztrációja
app.include_router(diarization_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}