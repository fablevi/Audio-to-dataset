package com.fablevi.audiotodataset.models.settings;

import com.fablevi.audiotodataset.models.settings.enums.Whisper;
import lombok.*;
import org.springframework.beans.factory.annotation.Value;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Getter
public class RunnerSettings {

    private Whisper whisper = Whisper.TURBO; //--backend whisper   -m ./backend/models/ggml-large-v3-turbo.bin
    private String vad = "firered"; // --vad -vm firered
    private String diarize = "sortformer"; //--diarize --diarize-method sortformer
    private boolean GPU = true;
    private String saveText = "/"; //--output-json-full   -of eredmeny_reszletes
    private String language = "en"; //-l hu

    public void setWhisper(Whisper w){
        this.whisper = w;
    }
}
