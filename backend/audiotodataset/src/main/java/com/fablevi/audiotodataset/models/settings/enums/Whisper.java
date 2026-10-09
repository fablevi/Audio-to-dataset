package com.fablevi.audiotodataset.models.settings.enums;

public enum Whisper {
    TURBO("turbo"),
    MEDIUM("medium"),
    LARGE("large");

    private final String value;

    Whisper(String value) {
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
