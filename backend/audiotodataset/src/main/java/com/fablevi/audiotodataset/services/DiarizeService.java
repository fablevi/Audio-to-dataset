package com.fablevi.audiotodataset.services;

import com.fablevi.audiotodataset.models.DiarizationResponse;
import com.fablevi.audiotodataset.models.settings.RunnerSettings;
import com.fablevi.audiotodataset.models.settings.enums.AiModalQuant;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import tools.jackson.databind.ObjectMapper;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

@Service
@Slf4j
public class DiarizeService {

    @Value("${audio.download.dir}")
    private String audioDownloadDir;

    @Value("${crispasr.dir}")
    private String crispAsrDir;

    @Value("${model.download.dir}")
    private String modelDownloadDir;

    @Autowired
    private SearchFolderService searchFolderService;

    @Autowired
    private ModelDownloadService mds;

    private final ObjectMapper objectMapper = new ObjectMapper();

    public DiarizationResponse runDiarization(RunnerSettings runnerSettings, AiModalQuant quant, String youtubeAudioId) {
        if (!searchFolderService.isAudioDownloaded(youtubeAudioId)) {
            log.warn("Audio file not found for YouTube ID: {}", youtubeAudioId);
            throw new RuntimeException("Audio file not found for YouTube ID: " + youtubeAudioId);
        }

        log.info("Audio already downloaded for ID: {}", youtubeAudioId);
        Path targetFile = Paths.get(audioDownloadDir, youtubeAudioId + ".wav");

        return executeCrispAsr(runnerSettings, quant, targetFile, youtubeAudioId);
    }

    private DiarizationResponse executeCrispAsr(RunnerSettings runnerSettings, AiModalQuant quant, Path audioFilePath, String youtubeAudioId) {
        try {
            String basePath = crispAsrDir.endsWith("/") ? crispAsrDir : crispAsrDir + "/";
            String crispAsrBin = basePath + "CrispASR/build/bin/crispasr";

            File binFile = new File(crispAsrBin);
            if (!binFile.exists()) {
                log.error("CrispASR binary not found at: {}", crispAsrBin);
                throw new RuntimeException("CrispASR binary not found at: " + crispAsrBin);
            }

            String modelFileName = mds.getWhisperLink(runnerSettings.getWhisper(), quant);
            String modelBasePath = modelDownloadDir.endsWith("/") ? modelDownloadDir : modelDownloadDir + "/";
            String modelPath = modelBasePath + modelFileName;

            if (!Files.exists(Paths.get(modelPath))) {
                log.error("Model file not found at: {}", modelPath);
                throw new RuntimeException("Model file not found at: " + modelPath);
            }
            log.info("Model file found at: {}", modelPath);

            Path outputJsonPrefix = Paths.get(audioDownloadDir + "/" + youtubeAudioId, "result_" + youtubeAudioId);
            Path expectedJsonPath = Paths.get(outputJsonPrefix.toString() + ".json");

            Path parentDir = outputJsonPrefix.getParent();
            if (parentDir != null && !Files.exists(parentDir)) {
                Files.createDirectories(parentDir);
                log.info("Created missing output directory: {}", parentDir);
            }

            List<String> cmd = new ArrayList<>();
            cmd.add(crispAsrBin);
            cmd.add("--backend");
            cmd.add("whisper");
            cmd.add("-m");
            cmd.add(modelPath);
            cmd.add("-f");
            cmd.add(audioFilePath.toString());
            cmd.add("--output-json-full");
            cmd.add("-of");
            cmd.add(outputJsonPrefix.toString());
            cmd.add("-l");
            cmd.add(runnerSettings.getLanguage());
            cmd.add("--diarize");
            cmd.add("--diarize-method");
            cmd.add(runnerSettings.getDiarize());
            cmd.add("--vad");
            cmd.add("-vm");
            cmd.add(runnerSettings.getVad());

            log.info("Starting CrispASR process with command: {}", String.join(" ", cmd));

            ProcessBuilder pb = new ProcessBuilder(cmd);
            pb.redirectErrorStream(true);
            Process process = pb.start();

            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    log.info("[CrispASR] {}", line);
                }
            }

            int exitCode = process.waitFor();

            if (exitCode != 0) {
                log.error("CrispASR process failed with exit code: {}", exitCode);
                throw new RuntimeException("CrispASR process failed with exit code: " + exitCode);
            }

            if (!Files.exists(expectedJsonPath)) {
                log.error("Expected output JSON file is missing: {}", expectedJsonPath);
                throw new RuntimeException("Expected output JSON file is missing: " + expectedJsonPath);
            }

            DiarizationResponse response = objectMapper.readValue(expectedJsonPath.toFile(), DiarizationResponse.class);
            log.info("Diarization completed successfully for ID: {}. Segments count: {}",
                    youtubeAudioId, response.getTranscription() != null ? response.getTranscription().size() : 0);

            // Files.deleteIfExists(expectedJsonPath);
            return response;

        } catch (IOException e) {
            log.error("IO Exception during CrispASR execution: {}", e.getMessage(), e);
            throw new RuntimeException("IO Error during execution: " + e.getMessage(), e);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.error("Process execution was interrupted: {}", e.getMessage(), e);
            throw new RuntimeException("Execution interrupted: " + e.getMessage(), e);
        }
    }
}