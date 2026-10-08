package com.fablevi.audiotodataset.models;

import lombok.*;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Getter
@Setter
public class YoutubeDownloadRequest {

    private String url;

    @Builder.Default
    private String quality = "best";

    @Builder.Default
    private String outputDir = "/tmp/yt_downloads";
}
