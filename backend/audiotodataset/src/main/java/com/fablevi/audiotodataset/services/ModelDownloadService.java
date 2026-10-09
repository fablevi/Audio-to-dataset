package com.fablevi.audiotodataset.services;

import com.fablevi.audiotodataset.models.settings.enums.AiModalQuant;
import com.fablevi.audiotodataset.models.settings.enums.Whisper;
import org.springframework.stereotype.Service;

@Service
public class ModelDownloadService {

    public String getDownloadLink(Whisper whisper, AiModalQuant quant){
        if(whisper == Whisper.LARGE){
            if(quant != AiModalQuant.FULL){
                return "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-" + quant + ".bin?download=true";
            }
            return "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin?download=true";
        }
        if (whisper == Whisper.MEDIUM){
            if(quant != AiModalQuant.FULL){
                return "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium-" + quant + ".bin?download=true";
            }
            return "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin?download=true";
        }
        if(whisper == Whisper.TURBO){
            if(quant != AiModalQuant.FULL){
                return "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-" + quant + ".bin?download=true";
            }
            return "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin?download=true";
        }
        return "";
    }
}
