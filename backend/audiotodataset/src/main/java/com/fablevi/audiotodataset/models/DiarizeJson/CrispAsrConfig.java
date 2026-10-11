package com.fablevi.audiotodataset.models.DiarizeJson;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
public class CrispAsrConfig {
    @JsonProperty("backend")
    private String backend;

    @JsonProperty("model")
    private String model;

    @JsonProperty("language")
    private String language;
}
