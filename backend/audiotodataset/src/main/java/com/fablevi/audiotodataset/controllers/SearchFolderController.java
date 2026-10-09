package com.fablevi.audiotodataset.controllers;

import com.fablevi.audiotodataset.services.SearchFolderService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/search")
public class SearchFolderController {

    @Autowired
    private SearchFolderService searchFolderService;

    @GetMapping("/{youtubeAudioId}")
    public ResponseEntity<Boolean> isAudioDownloaded(@PathVariable String youtubeAudioId) {
        return ResponseEntity.ok(searchFolderService.isAudioDownloaded(youtubeAudioId));
    }

    @GetMapping("/")
    public ResponseEntity<List<String>> getAllDownloadedAudioIds() {
        return ResponseEntity.ok(searchFolderService.getBackAllDownloadedAudioIds());
    }

    @GetMapping("/slices/{youtubeAudioId}")
    public ResponseEntity<List<String>> getSlicedAudioFiles(@PathVariable String youtubeAudioId) {
        return ResponseEntity.ok(searchFolderService.getBackSlicedAudioIds(youtubeAudioId));
    }
}