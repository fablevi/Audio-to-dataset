package com.fablevi.audiotodataset.controllers;

import com.fablevi.audiotodataset.models.DiarizationResponse;
import com.fablevi.audiotodataset.models.settings.RunnerSettings;
import com.fablevi.audiotodataset.models.settings.enums.AiModalQuant;
import com.fablevi.audiotodataset.services.DiarizeService;
import com.fablevi.audiotodataset.services.ModelDownloadService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/diarize")
@Slf4j
public class DiarizeController {

    @Autowired
    private ModelDownloadService mds;

    @Autowired
    private DiarizeService diarizeService;

    @PostMapping("/{youtubeAudioId}/{quant}")
    public ResponseEntity<Object> startDiarize(@PathVariable String youtubeAudioId, @PathVariable AiModalQuant quant, @RequestBody RunnerSettings incomingSettings) {
        log.info("Diarization started!");
        RunnerSettings runnerSettings = new RunnerSettings();

        runnerSettings = updateRunnerSettings(runnerSettings, incomingSettings);
        log.info(runnerSettings.toString());

        boolean isDownloaded = mds.DownloadWhisperModelToFolder(runnerSettings.getWhisper(), quant);

        if (!isDownloaded) {
            return ResponseEntity.internalServerError().body("Whisper is not downloaded");
        }

        try {
            DiarizationResponse response = diarizeService.runDiarization(runnerSettings, quant, youtubeAudioId);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Error during diarization process: {}", e.getMessage());
            return ResponseEntity.internalServerError().body("Diarization failed: " + e.getMessage());
        }
    }

    @GetMapping("/modelData")
    public RunnerSettings getBackJSON1(){
        return new RunnerSettings();
    }

    private RunnerSettings updateRunnerSettings(RunnerSettings runnerSettings, RunnerSettings incomingSettings){
        if (incomingSettings.getWhisper() != null) {
            runnerSettings.setWhisper(incomingSettings.getWhisper());
        }

        runnerSettings.setGPU(incomingSettings.isGPU());

        if (incomingSettings.getLanguage() != null && !incomingSettings.getLanguage().trim().isEmpty()) {
            runnerSettings.setLanguage(incomingSettings.getLanguage());
        }

        return runnerSettings;
    }

}
