package com.example.courseselection.controller;

import com.example.courseselection.entity.SystemConfig;
import com.example.courseselection.repository.SystemConfigRepository;
import com.example.courseselection.service.StudentService;
import com.example.courseselection.config.AllocationScheduler;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Map;

@RestController
@RequestMapping("/api/admin")
@RequiredArgsConstructor
public class AdminController {
    private final StudentService studentService;
    private final SystemConfigRepository systemConfigRepository;
    private final AllocationScheduler allocationScheduler;

    @PostMapping("/import-students")
    public ResponseEntity<?> importStudents(@RequestParam("file") MultipartFile file) {
        try {
            StudentService.ImportResult result = studentService.importStudents(file);
            return ResponseEntity.ok(Map.of(
                "importedCount", result.getImportedCount(),
                "skippedCount", result.getSkippedCount(),
                "skippedStudentNos", result.getSkippedStudentNos(),
                "passwords", result.getPasswords()
            ));
        } catch (IOException e) {
            return ResponseEntity.badRequest().body(Map.of("message", "文件解析失败: " + e.getMessage()));
        }
    }

    @PostMapping("/config")
    public ResponseEntity<?> updateConfig(@RequestBody ConfigRequest request) {
        try {
            // Update open time
            SystemConfig openTimeConfig = systemConfigRepository.findByKey("selection_open_time")
                    .orElse(new SystemConfig());
            openTimeConfig.setKey("selection_open_time");
            openTimeConfig.setValue(request.getOpenTime());
            systemConfigRepository.save(openTimeConfig);

            // Update duration
            SystemConfig durationConfig = systemConfigRepository.findByKey("selection_duration_minutes")
                    .orElse(new SystemConfig());
            durationConfig.setKey("selection_duration_minutes");
            durationConfig.setValue(String.valueOf(request.getDurationMinutes()));
            systemConfigRepository.save(durationConfig);

            // Reset allocation scheduler
            allocationScheduler.resetAllocationFlag();

            return ResponseEntity.ok(Map.of("message", "配置更新成功"));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of("message", "配置更新失败: " + e.getMessage()));
        }
    }

    @GetMapping("/config")
    public ResponseEntity<?> getConfig() {
        return ResponseEntity.ok(Map.of(
            "openTime", systemConfigRepository.findByKey("selection_open_time")
                    .map(SystemConfig::getValue).orElse(null),
            "durationMinutes", systemConfigRepository.findByKey("selection_duration_minutes")
                    .map(config -> Integer.parseInt(config.getValue())).orElse(30)
        ));
    }

    public static class ConfigRequest {
        private String openTime;
        private int durationMinutes;

        public String getOpenTime() { return openTime; }
        public void setOpenTime(String openTime) { this.openTime = openTime; }
        public int getDurationMinutes() { return durationMinutes; }
        public void setDurationMinutes(int durationMinutes) { this.durationMinutes = durationMinutes; }
    }
}
