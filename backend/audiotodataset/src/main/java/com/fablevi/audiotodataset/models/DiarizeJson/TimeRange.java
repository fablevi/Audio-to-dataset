package com.fablevi.audiotodataset.models.DiarizeJson;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
public class TimeRange {
    @JsonProperty("from")
    private String from;

    @JsonProperty("to")
    private String to;
}
