package com.fablevi.audiotodataset.models.DiarizeJson;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import java.util.List;

@Data
public class TranscriptionSegment {
    @JsonProperty("timestamps")
    private TimeRange timestamps;

    @JsonProperty("offsets")
    private OffsetRange offsets;

    @JsonProperty("speaker")
    private String speaker;

    @JsonProperty("text")
    private String text;

    @JsonProperty("chunk_id")
    private int chunkId;

    @JsonProperty("words")
    private List<WordItem> words;

    @JsonProperty("tokens")
    private List<TokenItem> tokens;
}
