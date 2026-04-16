package com.example.courseselection.service;

import com.example.courseselection.entity.Course;
import com.example.courseselection.repository.CourseRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class CourseService {
    private final CourseRepository courseRepository;

    public List<Course> getAllCourses() {
        return courseRepository.findAllByOrderByEnrolledCountAsc();
    }

    public Optional<Course> getCourseById(Long id) {
        return courseRepository.findById(id);
    }

    public List<Course> getAvailableCourses() {
        return courseRepository.findAvailableCourses();
    }

    public List<Course> getCoursesWithLowEnrollment() {
        return courseRepository.findCoursesWithLowEnrollment();
    }

    public Course save(Course course) {
        return courseRepository.save(course);
    }

    public void incrementEnrolledCount(Long courseId) {
        Course course = courseRepository.findById(courseId)
                .orElseThrow(() -> new RuntimeException("Course not found"));
        course.setEnrolledCount(course.getEnrolledCount() + 1);
        courseRepository.save(course);
    }

    public void decrementEnrolledCount(Long courseId) {
        Course course = courseRepository.findById(courseId)
                .orElseThrow(() -> new RuntimeException("Course not found));
        course.setEnrolledCount(course.getEnrolledCount() - 1);
        courseRepository.save(course);
    }
}
