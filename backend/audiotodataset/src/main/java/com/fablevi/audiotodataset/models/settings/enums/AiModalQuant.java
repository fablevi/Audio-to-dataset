package com.fablevi.audiotodataset.models.settings.enums;

public enum AiModalQuant {
    FULL("Full"),
    Q8("q8_0"),
    Q5("q5_0");

    private final String value;

    AiModalQuant(String value) {
        this.value = value;
    }

    public String getValue() {
        return value;
    }

    @Override
    public String toString() {
        return value;
    }
}
