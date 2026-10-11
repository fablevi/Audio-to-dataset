package com.fablevi.audiotodataset.models.DiarizeJson;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
public class TokenItem {
    @JsonProperty("text")
    private String text;

    @JsonProperty("p")
    private double p;

    @JsonProperty("t0")
    private long t0;

    @JsonProperty("t1")
    private long t1;

    @JsonProperty("offsets")
    private OffsetRange offsets;
}
