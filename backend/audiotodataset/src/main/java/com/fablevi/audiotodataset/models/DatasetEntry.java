package com.fablevi.audiotodataset.models;

import com.fablevi.audiotodataset.models.DiarizeJson.WordItem;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

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
    private List<WordItem> words;
}
