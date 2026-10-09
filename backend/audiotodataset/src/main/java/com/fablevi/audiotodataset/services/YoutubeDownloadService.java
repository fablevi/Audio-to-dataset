package com.fablevi.audiotodataset.services;

import com.fablevi.audiotodataset.models.YoutubeDownloadRequest;
import com.fablevi.audiotodataset.models.YoutubeDownloadResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.File;
import java.io.IOException;
import java.util.regex.Pattern;

@Service
public class YoutubeDownloadService {

    private static final Pattern VIDEO_ID_PATTERN =
            Pattern.compile("(?:watch\\?v=|youtu\\.be/|shorts/|embed/)([a-zA-Z0-9_-]{11})");

    @Value("${audio.download.dir}")
    private String defaultDir;

    @Autowired
    private SearchFolderService searchFolderService;

    public YoutubeDownloadResponse download(YoutubeDownloadRequest request) throws IOException, InterruptedException {

        String videoId = extractVideoId(request.getUrl());

        if (searchFolderService.isAudioDownloaded(videoId)) {
            String existingPath = defaultDir + "/" + videoId + ".wav";
            return YoutubeDownloadResponse.builder()
                    .path(existingPath)
                    .id(videoId)
                    .quality(request.getQuality())
                    .responseMessage("Video already downloaded")
                    .build();
        }

        String dir = request.getOutputDir() == null ? defaultDir : request.getOutputDir();
        File d = new File(dir);
        if (!d.exists()) {
            d.mkdirs();
        }

        String pattern = d.getAbsolutePath() + "/" + videoId + ".wav";

        ProcessBuilder pb = new ProcessBuilder(
                "yt-dlp",
                "-x",
                "--audio-format", "wav",
                "-o", pattern,
                request.getUrl()
        );
        pb.redirectErrorStream(true);

        Process process = pb.start();
        int exitCode = process.waitFor();

        if (exitCode != 0) {
            throw new IOException("Download failed (code " + exitCode + ")");
        }

        return YoutubeDownloadResponse.builder()
                .path(pattern)
                .id(videoId)
                .quality(request.getQuality())
                .responseMessage("Video downloaded")
                .build();
    }

    private String extractVideoId(String url) throws IOException {
        var matcher = VIDEO_ID_PATTERN.matcher(url);
        if (matcher.find()) {
            return matcher.group(1);
        }
        throw new IOException("Could not extract YouTube video ID from URL: " + url);
    }
}