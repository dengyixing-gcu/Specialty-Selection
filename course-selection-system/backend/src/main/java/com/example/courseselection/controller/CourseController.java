package com.example.courseselection.controller;

import com.example.courseselection.entity.Course;
import com.example.courseselection.service.CourseService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/courses")
@RequiredArgsConstructor
public class CourseController {
    private final CourseService courseService;

    @GetMapping
    public ResponseEntity<List<Course>> getAllCourses() {
        return ResponseEntity.ok(courseService.getAllCourses());
    }

    @GetMapping("/{id}")
    public ResponseEntity<?> getCourseById(@PathVariable Long id) {
        return courseService.getCourseById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/available")
    public ResponseEntity<List<Course>> getAvailableCourses() {
        return ResponseEntity.ok(courseService.getAvailableCourses());
    }

    @GetMapping("/status")
    public ResponseEntity<Map<String, Object>> getCourseStatus() {
        List<Course> courses = courseService.getAllCourses();
        int totalCapacity = courses.stream().mapToInt(Course::getCapacity).sum();
        int totalEnrolled = courses.stream().mapToInt(Course::getEnrolledCount).sum();

        return ResponseEntity.ok(Map.of(
            "courses", courses,
            "totalCapacity", totalCapacity,
            "totalEnrolled", totalEnrolled,
            "totalRemaining", totalCapacity - totalEnrolled
        ));
    }
}
