package com.fablevi.audiotodataset.services;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.Stream;

@Service
public class SearchFolderService {

    @Value("${audio.download.dir}")
    private String baseDir;

    public boolean isAudioDownloaded(String youtubeAudioId) {
        if (youtubeAudioId == null || youtubeAudioId.trim().isEmpty()) {
            return false;
        }

        Path targetFile = Paths.get(baseDir, youtubeAudioId + ".wav");
        return Files.exists(targetFile) && Files.isRegularFile(targetFile);
    }

    public List<String> getBackAllDownloadedAudioIds() {
        Path rootPath = Paths.get(baseDir);
        if (!Files.exists(rootPath) || !Files.isDirectory(rootPath)) {
            return new ArrayList<>();
        }

        try (Stream<Path> stream = Files.list(rootPath)) {
            return stream
                    .filter(Files::isRegularFile)
                    .map(Path::getFileName)
                    .map(Path::toString)
                    .filter(name -> name.toLowerCase().endsWith(".wav"))
                    .map(name -> name.substring(0, name.lastIndexOf('.')))
                    .collect(Collectors.toList());
        } catch (IOException e) {
            return new ArrayList<>();
        }
    }

    public List<String> getBackSlicedAudioIds(String youtubeAudioId) {
        if (youtubeAudioId == null || youtubeAudioId.trim().isEmpty()) {
            return new ArrayList<>();
        }

        Path slicedFolderPath = Paths.get(baseDir, youtubeAudioId);

        if (!Files.exists(slicedFolderPath) || !Files.isDirectory(slicedFolderPath)) {
            return new ArrayList<>();
        }

        try (Stream<Path> stream = Files.list(slicedFolderPath)) {
            return stream
                    .filter(Files::isRegularFile)
                    .map(path -> path.getFileName().toString())
                    .collect(Collectors.toList());
        } catch (IOException e) {
            return new ArrayList<>();
        }
    }
}