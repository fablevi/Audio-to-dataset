package com.fablevi.audiotodataset.controllers;

import com.fablevi.audiotodataset.models.YoutubeDownloadRequest;
import com.fablevi.audiotodataset.models.YoutubeDownloadResponse;
import com.fablevi.audiotodataset.services.YoutubeDownloadService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/youtube")
public class YoutubeDownloadController {

    @Autowired
    private YoutubeDownloadService service;

    @PostMapping("/download")
    public ResponseEntity<YoutubeDownloadResponse> download(@RequestBody YoutubeDownloadRequest request) {
        try {
            YoutubeDownloadResponse response = service.download(request);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            return ResponseEntity.status(500).body(YoutubeDownloadResponse.builder()
                    .responseMessage(e.getMessage())
                    .build());
        }
    }
}