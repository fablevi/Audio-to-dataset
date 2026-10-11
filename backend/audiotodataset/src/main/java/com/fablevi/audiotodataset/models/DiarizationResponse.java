package com.fablevi.audiotodataset.models;

import com.fablevi.audiotodataset.models.DiarizeJson.CrispAsrConfig;
import com.fablevi.audiotodataset.models.DiarizeJson.TranscriptionSegment;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import java.util.List;

@Data
public class DiarizationResponse {
    @JsonProperty("crispasr")
    private CrispAsrConfig crispasr;

    @JsonProperty("transcription")
    private List<TranscriptionSegment> transcription;
}
