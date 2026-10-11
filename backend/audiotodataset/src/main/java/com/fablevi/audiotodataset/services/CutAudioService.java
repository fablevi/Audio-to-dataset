package com.fablevi.audiotodataset.services;

import com.fablevi.audiotodataset.exceptions.CutAudioException;
import com.fablevi.audiotodataset.models.DatasetEntry;
import com.fablevi.audiotodataset.models.DiarizationResponse;
import com.fablevi.audiotodataset.models.DiarizeJson.TranscriptionSegment;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import tools.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

@Service
@Slf4j
public class CutAudioService {

    @Value("${audio.download.dir}")
    private String audioDownloadDir;

    private final ObjectMapper objectMapper = new ObjectMapper();

    public List<DatasetEntry> cutAudio(DiarizationResponse response, String youtubeAudioId) {
        log.info("Starting audio cutting process for YouTube ID: {}", youtubeAudioId);

        if (response == null || response.getTranscription() == null) {
            log.error("Diarization response or transcription is null for ID: {}", youtubeAudioId);
            throw new CutAudioException("Diarization response or transcription is null for ID: " + youtubeAudioId);
        }

        Path audioSubDir = Paths.get(audioDownloadDir, youtubeAudioId, "audio");
        Path datasetJsonPath = Paths.get(audioDownloadDir, youtubeAudioId, "dataset.json");
        Path sourceAudioPath = Paths.get(audioDownloadDir, youtubeAudioId + ".wav");

        log.info("Source audio path: {}", sourceAudioPath);
        log.info("Target audio sub-directory: {}", audioSubDir);
        log.info("Dataset JSON target path: {}", datasetJsonPath);

        if (!Files.exists(sourceAudioPath)) {
            log.error("Source audio file not found at: {}", sourceAudioPath);
            throw new CutAudioException("Source audio file not found at: " + sourceAudioPath);
        }

        try {
            if (Files.exists(audioSubDir)) {
                log.info("Audio sub-directory already exists. Cleaning up old files...");
                deleteDirectoryRecursively(audioSubDir);
            }
            Files.createDirectories(audioSubDir);
            log.info("Created fresh audio sub-directory successfully.");
        } catch (IOException e) {
            log.error("Failed to initialize audio directory for ID: {}. Error: {}", youtubeAudioId, e.getMessage(), e);
            throw new CutAudioException("Failed to initialize audio directory for ID: " + youtubeAudioId, e);
        }

        List<DatasetEntry> datasetList = new ArrayList<>();
        List<TranscriptionSegment> segments = response.getTranscription();
        log.info("Total segments to process: {}", segments.size());

        for (int i = 0; i < segments.size(); i++) {
            TranscriptionSegment segment = segments.get(i);

            if (segment.getOffsets() == null) {
                log.warn("Segment at index {} has null offsets, skipping.", i);
                continue;
            }

            long startMs = segment.getOffsets().getFrom();
            long endMs = segment.getOffsets().getTo();

            double startSec = startMs / 1000.0;
            double durationSec = (endMs - startMs) / 1000.0;

            if (durationSec <= 0) {
                log.warn("Segment at index {} has invalid duration ({:.3f}s), skipping.", i, durationSec);
                continue;
            }

            String rawSpeaker = "0";
            if (segment.getSpeaker() != null) {
                rawSpeaker = segment.getSpeaker().trim();
            }

            String speakerNum = rawSpeaker.replaceAll("[^0-9]", "");
            if (speakerNum.isEmpty()) {
                speakerNum = "0";
            }

            String formattedSpeakerId = youtubeAudioId + "_" + speakerNum;

            log.debug("Raw speaker from segment: '{}' -> Parsed number: '{}' -> Formatted ID: '{}'",
                    segment.getSpeaker(), speakerNum, formattedSpeakerId);

            String outputFileName = i + ".wav";
            Path outputFilePath = audioSubDir.resolve(outputFileName);

            Path relativeAudioPath = datasetJsonPath.getParent().relativize(outputFilePath);

            log.debug("Processing segment {}: from {} ms to {} ms (start: {:.3f}s, duration: {:.3f}s) -> {}",
                    i, startMs, endMs, startSec, durationSec, outputFilePath);

            List<String> cmd = List.of(
                    "ffmpeg",
                    "-y",
                    "-ss", String.format(Locale.US, "%.3f", startSec),
                    "-i", sourceAudioPath.toString(),
                    "-t", String.format(Locale.US, "%.3f", durationSec),
                    "-c:a", "pcm_s16le",
                    "-ar", "48000",
                    "-ac", "1",
                    "-loglevel", "quiet",
                    outputFilePath.toString()
            );

            try {
                ProcessBuilder pb = new ProcessBuilder(cmd);
                Process process = pb.start();
                int exitCode = process.waitFor();

                if (exitCode != 0) {
                    log.error("FFmpeg failed with exit code {} for segment index {}", exitCode, i);
                    throw new CutAudioException("FFmpeg failed with exit code " + exitCode + " for segment index " + i);
                }

                DatasetEntry entry = DatasetEntry.builder()
                        .fromMs(startMs)
                        .toMs(endMs)
                        .speaker(formattedSpeakerId)
                        .audioPath(relativeAudioPath.toString())
                        .text(segment.getText())
                        .build();

                datasetList.add(entry);

            } catch (IOException | InterruptedException e) {
                if (e instanceof InterruptedException) {
                    Thread.currentThread().interrupt();
                }
                log.error("Error processing audio segment {} for ID {}: {}", i, youtubeAudioId, e.getMessage(), e);
                throw new CutAudioException("Error processing audio segment " + i + " for ID " + youtubeAudioId, e);
            }
        }

        log.info("Writing dataset.json containing {} entries to: {}", datasetList.size(), datasetJsonPath);
        objectMapper.writerWithDefaultPrettyPrinter().writeValue(datasetJsonPath.toFile(), datasetList);
        log.info("dataset.json successfully written.");

        log.info("Audio cutting process finished successfully for ID: {}", youtubeAudioId);
        return datasetList;
    }

    private void deleteDirectoryRecursively(Path path) throws IOException {
        Files.walkFileTree(path, new SimpleFileVisitor<Path>() {
            @Override
            public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
                Files.delete(file);
                return FileVisitResult.CONTINUE;
            }

            @Override
            public FileVisitResult postVisitDirectory(Path dir, IOException exc) throws IOException {
                Files.delete(dir);
                return FileVisitResult.CONTINUE;
            }
        });
    }
}