package com.example.courseselection.controller;

import com.example.courseselection.entity.Selection;
import com.example.courseselection.entity.Student;
import com.example.courseselection.service.SelectionService;
import com.example.courseselection.service.StudentService;
import com.example.courseselection.util.JwtUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import jakarta.servlet.http.HttpServletRequest;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/selection")
@RequiredArgsConstructor
public class SelectionController {
    private final SelectionService selectionService;
    private final StudentService studentService;
    private final JwtUtil jwtUtil;

    @PostMapping("/select")
    public ResponseEntity<?> selectCourse(@RequestBody SelectRequest request, HttpServletRequest httpRequest) {
        String studentNo = getStudentNoFromRequest(httpRequest);
        if (studentNo == null) {
            return ResponseEntity.status(401).body(Map.of("message", "未登录"));
        }

        Student student = studentService.findByStudentNo(studentNo);
        if (student == null) {
            return ResponseEntity.badRequest().body(Map.of("message", "学生不存在"));
        }

        SelectionService.SelectionResult result = selectionService.selectCourse(student.getId(), request.getCourseId());

        if (result.isSuccess()) {
            return ResponseEntity.ok(Map.of(
                "success", true,
                "message", result.getMessage(),
                "selection", Map.of(
                    "courseName", result.getSelection().getCourse().getName(),
                    "selectedAt", result.getSelection().getSelectedAt().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
                )
            ));
        } else {
            return ResponseEntity.badRequest().body(Map.of(
                "success", false,
                "message", result.getMessage()
            ));
        }
    }

    @GetMapping("/status")
    public ResponseEntity<?> getSelectionStatus(HttpServletRequest httpRequest) {
        String studentNo = getStudentNoFromRequest(httpRequest);
        if (studentNo == null) {
            return ResponseEntity.status(401).body(Map.of("message", "未登录"));
        }

        Student student = studentService.findByStudentNo(studentNo);
        if (student == null) {
            return ResponseEntity.badRequest().body(Map.of("message", "学生不存在"));
        }

        Optional<Selection> selection = selectionService.getStudentSelection(student.getId());
        boolean isOpen = selectionService.isSelectionOpen();
        LocalDateTime openTime = selectionService.getSelectionOpenTime();
        int durationMinutes = selectionService.getSelectionDurationMinutes();

        return ResponseEntity.ok(Map.of(
            "hasSelected", selection.isPresent(),
            "isOpen", isOpen,
            "openTime", openTime != null ? openTime.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME) : null,
            "durationMinutes", durationMinutes,
            "selection", selection.map(s -> Map.of(
                "courseName", s.getCourse().getName(),
                "selectedAt", s.getSelectedAt().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME),
                "isAutoAllocated", s.getAutoAllocated()
            )).orElse(null)
        ));
    }

    @GetMapping("/result")
    public ResponseEntity<?> getSelectionResult(HttpServletRequest httpRequest) {
        String studentNo = getStudentNoFromRequest(httpRequest);
        if (studentNo == null) {
            return ResponseEntity.status(401).body(Map.of("message", "未登录"));
        }

        Student student = studentService.findByStudentNo(studentNo);
        if (student == null) {
            return ResponseEntity.badRequest().body(Map.of("message", "学生不存在"));
        }

        Optional<Selection> selection = selectionService.getStudentSelection(student.getId());

        if (selection.isEmpty()) {
            return ResponseEntity.ok(Map.of(
                "hasSelected", false,
                "message", "您尚未选课"
            ));
        }

        Selection s = selection.get();
        return ResponseEntity.ok(Map.of(
            "hasSelected", true,
            "courseName", s.getCourse().getName(),
            "courseId", s.getCourse().getId(),
            "selectedAt", s.getSelectedAt().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME),
            "isAutoAllocated", s.getAutoAllocated()
        ));
    }

    private String getStudentNoFromRequest(HttpServletRequest request) {
        String authHeader = request.getHeader("Authorization");
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7);
            if (jwtUtil.validateToken(token)) {
                return jwtUtil.getStudentNoFromToken(token);
            }
        }
        return null;
    }

    public static class SelectRequest {
        private Long courseId;

        public Long getCourseId() { return courseId; }
        public void setCourseId(Long courseId) { this.courseId = courseId; }
    }
}
