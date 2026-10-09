package com.fablevi.audiotodataset.models.settings;

import com.fablevi.audiotodataset.models.settings.enums.Whisper;
import lombok.*;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Getter
public class RunnerSettings {
    private Whisper whisper; //--backend whisper   -m ./backend/models/ggml-large-v3-turbo.bin
    private String whisperModelFolder = ""; // ./backend/models/
    private String vad = "firered"; // --vad -vm firered
    private String diarize = "sortformer"; //--diarize --diarize-method sortformer
    private boolean GPU = true;
    private String saveText = "/"; //--output-json-full   -of eredmeny_reszletes
    private String language = "en"; //-l hu
}
