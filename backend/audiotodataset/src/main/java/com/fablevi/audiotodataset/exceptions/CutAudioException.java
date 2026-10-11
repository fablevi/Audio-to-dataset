package com.fablevi.audiotodataset.exceptions;

public class CutAudioException extends RuntimeException {
    public CutAudioException(String message) {
        super(message);
    }

    public CutAudioException(String message, Throwable cause) {
        super(message, cause);
    }
}
