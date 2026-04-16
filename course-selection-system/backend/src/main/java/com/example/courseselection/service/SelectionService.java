package com.example.courseselection.service;

import com.example.courseselection.entity.Course;
import com.example.courseselection.entity.Selection;
import com.example.courseselection.entity.Student;
import com.example.courseselection.entity.SystemConfig;
import com.example.courseselection.repository.CourseRepository;
import com.example.courseselection.repository.SelectionRepository;
import com.example.courseselection.repository.SystemConfigRepository;
import com.example.courseselection.util.RedisLockUtil;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Optional;

@Service
@RequiredArgsConstructor
@Slf4j
public class SelectionService {
    private final SelectionRepository selectionRepository;
    private final CourseRepository courseRepository;
    private final SystemConfigRepository systemConfigRepository;
    private final RedisLockUtil redisLockUtil;

    @Transactional
    public SelectionResult selectCourse(Long studentId, Long courseId) {
        // Check if student has already selected a course
        if (selectionRepository.existsByStudentId(studentId)) {
            return SelectionResult.alreadySelected();
        }

        // Check rate limit
        if (!redisLockUtil.tryRateLimit(String.valueOf(studentId))) {
            return SelectionResult.rateLimited();
        }

        // Check selection time
        if (!isSelectionOpen()) {
            return SelectionResult.notOpen();
        }

        // Try to lock course
        if (!redisLockUtil.tryLockCourse(courseId)) {
            return SelectionResult.courseBusy();
        }

        try {
            // Try to lock student
            if (!redisLockUtil.tryLockStudent(studentId)) {
                return SelectionResult.studentBusy();
            }

            try {
                // Check course availability with optimistic locking
                Course course = courseRepository.findById(courseId)
                        .orElse(null);

                if (course == null) {
                    return SelectionResult.courseNotFound();
                }

                if (course.isFull()) {
                    return SelectionResult.courseFull();
                }

                // Increment enrolled count with optimistic locking
                course.setEnrolledCount(course.getEnrolledCount() + 1);
                courseRepository.save(course);

                // Create selection record
                Student student = new Student();
                student.setId(studentId);

                Selection selection = new Selection();
                selection.setStudent(student);
                selection.setCourse(course);
                selection.setSelectedAt(LocalDateTime.now());
                selection.setAutoAllocated(false);

                selection = selectionRepository.save(selection);

                log.info("Student {} selected course {}", studentId, courseId);
                return SelectionResult.success(selection);

            } finally {
                redisLockUtil.unlockStudent(studentId);
            }
        } finally {
            redisLockUtil.unlockCourse(courseId);
        }
    }

    public boolean isSelectionOpen() {
        Optional<SystemConfig> openTimeConfig = systemConfigRepository.findByKey("selection_open_time");
        Optional<SystemConfig> durationConfig = systemConfigRepository.findByKey("selection_duration_minutes");

        if (openTimeConfig.isEmpty() || durationConfig.isEmpty()) {
            return false;
        }

        LocalDateTime openTime = LocalDateTime.parse(openTimeConfig.get().getValue(), DateTimeFormatter.ISO_LOCAL_DATE_TIME);
        int durationMinutes = Integer.parseInt(durationConfig.get().getValue());
        LocalDateTime closeTime = openTime.plusMinutes(durationMinutes);
        LocalDateTime now = LocalDateTime.now();

        return now.isAfter(openTime) && now.isBefore(closeTime);
    }

    public LocalDateTime getSelectionOpenTime() {
        return systemConfigRepository.findByKey("selection_open_time")
                .map(config -> LocalDateTime.parse(config.getValue(), DateTimeFormatter.ISO_LOCAL_DATE_TIME))
                .orElse(null);
    }

    public int getSelectionDurationMinutes() {
        return systemConfigRepository.findByKey("selection_duration_minutes")
                .map(config -> Integer.parseInt(config.getValue()))
                .orElse(30);
    }

    public Optional<Selection> getStudentSelection(Long studentId) {
        return selectionRepository.findByStudentIdWithCourse(studentId);
    }

    public static class SelectionResult {
        private final boolean success;
        private final String message;
        private final Selection selection;

        private SelectionResult(boolean success, String message, Selection selection) {
            this.success = success;
            this.message = message;
            this.selection = selection;
        }

        public static SelectionResult success(Selection selection) {
            return new SelectionResult(true, "选课成功", selection);
        }

        public static SelectionResult alreadySelected() {
            return new SelectionResult(false, "您已选课，不可重复选择", null);
        }

        public static SelectionResult courseFull() {
            return new SelectionResult(false, "课程已满", null);
        }

        public static SelectionResult courseNotFound() {
            return new SelectionResult(false, "课程不存在", null);
        }

        public static SelectionResult notOpen() {
            return new SelectionResult(false, "选课未开放或已结束", null);
        }

        public static SelectionResult rateLimited() {
            return new SelectionResult(false, "请求过于频繁，请稍后再试", null);
        }

        public static SelectionResult courseBusy() {
            return new SelectionResult(false, "系统繁忙，请稍后再试", null);
        }

        public static SelectionResult studentBusy() {
            return new SelectionResult(false, "系统繁忙，请稍后再试", null);
        }

        public boolean isSuccess() { return success; }
        public String getMessage() { return message; }
        public Selection getSelection() { return selection; }
    }
}
