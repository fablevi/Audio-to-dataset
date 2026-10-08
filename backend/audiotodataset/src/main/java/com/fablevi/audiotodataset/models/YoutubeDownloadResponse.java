package com.fablevi.audiotodataset.models;

import lombok.*;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Getter
@Setter
public class YoutubeDownloadResponse {
    private String path;
    private String id;
    private String quality;
    private String responseMessage;
}
