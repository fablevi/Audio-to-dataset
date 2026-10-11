package com.fablevi.audiotodataset.models.DiarizeJson;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
public class OffsetRange {
    @JsonProperty("from")
    private long from;

    @JsonProperty("to")
    private long to;
}
