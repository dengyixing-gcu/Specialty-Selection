package com.example.courseselection.config;

import com.example.courseselection.entity.Course;
import com.example.courseselection.entity.SystemConfig;
import com.example.courseselection.repository.CourseRepository;
import com.example.courseselection.repository.SystemConfigRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

@Component
@RequiredArgsConstructor
@Slf4j
public class DataInitializer implements CommandLineRunner {
    private final CourseRepository courseRepository;
    private final SystemConfigRepository systemConfigRepository;

    @Override
    public void run(String... args) {
        initializeCourses();
        initializeSystemConfig();
    }

    private void initializeCourses() {
        if (courseRepository.count() > 0) {
            log.info("Courses already initialized, skipping...");
            return;
        }

        String[] courseNames = {
            "高等数学", "线性代数", "概率论与数理统计",
            "大学物理", "数据结构与算法", "操作系统",
            "计算机网络", "数据库原理", "软件工程"
        };

        for (String courseName : courseNames) {
            Course course = new Course();
            course.setName(courseName);
            course.setCapacity(90);
            course.setEnrolledCount(0);
            courseRepository.save(course);
            log.info("Created course: {}", courseName);
        }

        log.info("All courses initialized successfully");
    }

    private void initializeSystemConfig() {
        if (systemConfigRepository.existsById("selection_open_time")) {
            log.info("System config already initialized, skipping...");
            return;
        }

        // Default: selection opens tomorrow at 9:00 AM
        LocalDateTime openTime = LocalDateTime.now().plusDays(1).withHour(9).withMinute(0).withSecond(0);
        DateTimeFormatter formatter = DateTimeFormatter.ISO_LOCAL_DATE_TIME;

        SystemConfig openTimeConfig = new SystemConfig();
        openTimeConfig.setKey("selection_open_time");
        openTimeConfig.setValue(openTime.format(formatter));
        systemConfigRepository.save(openTimeConfig);

        SystemConfig durationConfig = new SystemConfig();
        durationConfig.setKey("selection_duration_minutes");
        durationConfig.setValue("30");
        systemConfigRepository.save(durationConfig);

        SystemConfig adminPasswordConfig = new SystemConfig();
        adminPasswordConfig.setKey("admin_password");
        adminPasswordConfig.setValue("admin123");
        systemConfigRepository.save(adminPasswordConfig);

        log.info("System config initialized successfully");
    }
}
