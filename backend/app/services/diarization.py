import os
import re
import subprocess
import tempfile
import logging
from app.models.diarization import DiarizationResponse, SpeakerTurn

logger = logging.getLogger(__name__)

# BASE_DIR feloldása
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Helyes útvonalak (egy 'backend' mappával kevesebb)
CRISPASR_BIN = os.path.join(BASE_DIR, "../CrispASR/build/bin/crispasr") if not os.path.exists(os.path.join(BASE_DIR, "CrispASR")) else os.path.join(BASE_DIR, "CrispASR/build/bin/crispasr")
MODEL_PATH = os.path.join(BASE_DIR, "models/moss-transcribe-diarize-0.9b-f16.gguf")

class DiarizationService:

    async def process_audio(
        self, file_bytes: bytes, file_extension: str, language: str = "en"
    ) -> DiarizationResponse:
        
        # Ellenőrizzük, hogy léteznek-e a fájlok
        if not os.path.exists(CRISPASR_BIN):
            # Próbáljuk meg a projekt gyökeréből kitalálni
            alt_bin = os.path.abspath(os.path.join(BASE_DIR, "..", "CrispASR/build/bin/crispasr"))
            if os.path.exists(alt_bin):
                bin_to_use = alt_bin
            else:
                raise RuntimeError(f"CrispASR bináris nem található: {CRISPASR_BIN}")
        else:
            bin_to_use = CRISPASR_BIN

        if not os.path.exists(MODEL_PATH):
            raise RuntimeError(f"A modell fájl nem található ezen az útvonalon: {MODEL_PATH}")

        suffix = file_extension if file_extension.startswith(".") else f".{file_extension}"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
            temp_audio.write(file_bytes)
            temp_audio_path = temp_audio.name

        try:
            cmd = [
                bin_to_use,
                "--backend", "moss-diarize",
                "-m", MODEL_PATH,
                "-f", temp_audio_path,
                "-l", language
            ]

            logger.info(f"CLI futtatása: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            raw_output = result.stdout + "\n" + result.stderr

            segments_data = []
            unique_speakers = set()

            # Minta: [0.08][S01] Szöveg...[5.99]
            timestamp_pattern = re.compile(
                r"\[(?P<start>\d+\.\d+)\]\s*\[(?P<speaker>S\d+|SPEAKER_\d+|spk\d+)\]\s*(?P<text>.*?)(?=\[\d+\.\d+\]|$)",
                re.DOTALL | re.IGNORECASE,
            )

            matches = list(timestamp_pattern.finditer(raw_output))

            if matches:
                for i, match in enumerate(matches):
                    spk = match.group("speaker").upper()
                    start_time = float(match.group("start"))
                    clean_text = match.group("text").strip()

                    if i + 1 < len(matches):
                        end_time = float(matches[i + 1].group("start"))
                    else:
                        end_time = round(start_time + 3.0, 2)

                    if clean_text:
                        unique_speakers.add(spk)
                        segments_data.append(
                            SpeakerTurn(
                                speaker=spk,
                                start=round(start_time, 2),
                                end=round(end_time, 2),
                                text=clean_text,
                            )
                        )
            else:
                fallback_pattern = re.compile(
                    r"\((?:Speaker|S)\s*(?P<speaker>\d+|S\d+)\)\s*(?P<text>[^\(]+)", re.IGNORECASE
                )
                fb_matches = list(fallback_pattern.finditer(raw_output))
                current_time = 0.0

                for match in fb_matches:
                    spk = f"S{match.group('speaker').zfill(2)}"
                    clean_text = match.group("text").strip()
                    duration = max(1.5, round(len(clean_text) / 15.0, 2))

                    if clean_text:
                        unique_speakers.add(spk)
                        segments_data.append(
                            SpeakerTurn(
                                speaker=spk,
                                start=round(current_time, 2),
                                end=round(current_time + duration, 2),
                                text=clean_text,
                            )
                        )
                        current_time += duration

            return DiarizationResponse(
                speaker_count=len(unique_speakers),
                speakers=sorted(list(unique_speakers)),
                segments=segments_data,
            )

        except subprocess.CalledProcessError as e:
            logger.error(f"CLI Hiba: {e.stderr}")
            raise RuntimeError(f"CrispASR CLI futtatási hiba: {e.stderr}")
        finally:
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)


diarization_service = DiarizationService()