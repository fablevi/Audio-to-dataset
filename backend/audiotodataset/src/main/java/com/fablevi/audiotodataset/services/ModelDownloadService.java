package com.fablevi.audiotodataset.services;

import com.fablevi.audiotodataset.models.settings.enums.AiModalQuant;
import com.fablevi.audiotodataset.models.settings.enums.Whisper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;

@Slf4j
@Service
public class ModelDownloadService {

    @Value("${model.download.dir}")
    private String modelDownloadDir;

    private final String huggingfaceLink = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/";

    public String getWhisperLink(Whisper whisper, AiModalQuant quant){
        if(whisper == Whisper.LARGE){
            if(quant != AiModalQuant.FULL){
                return "ggml-large-v3-" + quant + ".bin";
            }
            return "ggml-large-v3.bin";
        }
        if (whisper == Whisper.MEDIUM){
            if(quant != AiModalQuant.FULL){
                return "ggml-medium-" + quant + ".bin";
            }
            return "ggml-medium.bin";
        }
        if(whisper == Whisper.TURBO){
            if(quant != AiModalQuant.FULL){
                return "ggml-large-v3-turbo-" + quant + ".bin";
            }
            return "ggml-large-v3-turbo.bin";
        }
        return "";
    }

    public boolean DownloadWhisperModelToFolder(Whisper whisper, AiModalQuant quant){
        String modelFileName = getWhisperLink(whisper, quant);
        if (modelFileName.isEmpty()) {
            log.error("Invalid whisper model or quantization configuration!");
            return false;
        }

        String fullUrl = huggingfaceLink + modelFileName + "?download=true";
        log.info("Model checking/downloading started!");
        log.info("Download Link: {}", fullUrl);

        try {
            Path targetDir = Path.of(modelDownloadDir);
            if (!Files.exists(targetDir)) {
                Files.createDirectories(targetDir);
            }
            log.info("Target folder: {}", targetDir);

            Path targetFile = targetDir.resolve(modelFileName);

            if (Files.exists(targetFile)) {
                log.info("Model file already exists, skipping download: {}", targetFile);
                return true;
            }

            log.info("Model file not found locally, downloading from Hugging Face...");
            URI uri = URI.create(fullUrl);

            HttpClient client = HttpClient.newBuilder()
                    .followRedirects(HttpClient.Redirect.NORMAL)
                    .build();

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(uri)
                    .GET()
                    .build();

            HttpResponse<Path> response = client.send(request, HttpResponse.BodyHandlers.ofFile(targetFile));

            if (response.statusCode() == 200) {
                log.info("Model downloaded successfully to: {}", targetFile);
                return true;
            } else {
                log.error("Failed to download model. HTTP Status code: {}", response.statusCode());
                return false;
            }

        } catch (IOException | InterruptedException e) {
            Thread.currentThread().interrupt();
            log.error("Error during model download: {}", e.getMessage(), e);
            return false;
        }
    }
}