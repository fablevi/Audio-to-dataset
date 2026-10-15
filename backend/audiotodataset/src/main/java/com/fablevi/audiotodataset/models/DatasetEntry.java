package com.fablevi.audiotodataset.models;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DatasetEntry {
    private long fromMs;
    private long toMs;
    private String speaker;
    private String audioPath;
    private String text;
    private String emotionPrediction;
    private double confidence;
}
