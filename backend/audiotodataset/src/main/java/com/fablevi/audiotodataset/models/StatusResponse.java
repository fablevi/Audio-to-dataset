package com.fablevi.audiotodataset.models;

import com.fablevi.audiotodataset.models.enums.TaskStatus;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class StatusResponse {
    private String taskId;
    private TaskStatus status;
    private boolean isRunning;
    private String error;
}