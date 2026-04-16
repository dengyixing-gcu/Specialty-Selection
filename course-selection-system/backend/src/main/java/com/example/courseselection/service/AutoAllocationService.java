package com.example.courseselection.service;

import com.example.courseselection.entity.Course;
import com.example.courseselection.entity.Selection;
import com.example.courseselection.entity.Student;
import com.example.courseselection.repository.CourseRepository;
import com.example.courseselection.repository.SelectionRepository;
import com.example.courseselection.repository.StudentRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDateTime;
import java.util.*;

@Service
@RequiredArgsConstructor
@Slf4j
public class AutoAllocationService {
    private final StudentRepository studentRepository;
    private final CourseRepository courseRepository;
    private final SelectionRepository selectionRepository;

    @Transactional
    public AllocationResult allocateUnselectedStudents() {
        // Get all students
        List<Student> allStudents = studentRepository.findAll();

        // Get all selected student IDs
        List<Long> selectedStudentIds = selectionRepository.findAllSelectedStudentIds();

        // Find unselected students
        Set<Long> selectedSet = new HashSet<>(selectedStudentIds);
        List<Student> unselectedStudents = new ArrayList<>();
        for (Student student : allStudents) {
            if (!selectedSet.contains(student.getId())) {
                unselectedStudents.add(student);
            }
        }

        if (unselectedStudents.isEmpty()) {
            log.info("No unselected students found, skipping allocation");
            return new AllocationResult(0, 0, 0);
        }

        log.info("Found {} unselected students", unselectedStudents.size());

        // Get all courses
        List<Course> courses = courseRepository.findAll();

        // Phase 1: Fill courses with less than 30 students
        int phase1Allocated = allocatePhase1(unselectedStudents, courses);

        // Phase 2: Distribute remaining students to courses with available capacity
        int phase2Allocated = allocatePhase2(unselectedStudents, courses);

        log.info("Allocation complete: phase1={}, phase2={}", phase1Allocated, phase2Allocated);
        return new AllocationResult(unselectedStudents.size(), phase1Allocated, phase2Allocated);
    }

    private int allocatePhase1(List<Student> unselectedStudents, List<Course> courses) {
        int allocated = 0;
        List<Student> remainingStudents = new ArrayList<>(unselectedStudents);

        // Find courses with less than 30 students
        List<Course> lowEnrollmentCourses = new ArrayList<>();
        for (Course course : courses) {
            if (course.getEnrolledCount() < 30) {
                lowEnrollmentCourses.add(course);
            }
        }

        if (lowEnrollmentCourses.isEmpty()) {
            return 0;
        }

        // Randomly distribute students to low enrollment courses
        Random random = new Random();
        Iterator<Student> studentIterator = remainingStudents.iterator();

        while (studentIterator.hasNext() && !lowEnrollmentCourses.isEmpty()) {
            Student student = studentIterator.next();

            // Find a course that still needs students
            Course targetCourse = null;
            for (Course course : lowEnrollmentCourses) {
                if (course.getEnrolledCount() < 30) {
                    targetCourse = course;
                    break;
                }
            }

            if (targetCourse == null) {
                break;
            }

            // Allocate student to course
            allocateStudentToCourse(student, targetCourse);
            studentIterator.remove();
            allocated++;

            // Check if course is now at 30
            if (targetCourse.getEnrolledCount() >= 30) {
                lowEnrollmentCourses.remove(targetCourse);
            }
        }

        log.info("Phase 1: Allocated {} students to low enrollment courses", allocated);
        return allocated;
    }

    private int allocatePhase2(List<Student> remainingStudents, List<Course> courses) {
        int allocated = 0;

        // Get courses with available capacity
        List<Course> availableCourses = new ArrayList<>();
        for (Course course : courses) {
            if (!course.isFull()) {
                availableCourses.add(course);
            }
        }

        if (availableCourses.isEmpty()) {
            return 0;
        }

        // Randomly distribute remaining students
        Random random = new Random();
        for (Student student : remainingStudents) {
            if (availableCourses.isEmpty()) {
                break;
            }

            // Select a random course with available capacity
            int index = random.nextInt(availableCourses.size());
            Course targetCourse = availableCourses.get(index);

            // Allocate student to course
            allocateStudentToCourse(student, targetCourse);
            allocated++;

            // Remove course if it's now full
            if (targetCourse.isFull()) {
                availableCourses.remove(index);
            }
        }

        log.info("Phase 2: Allocated {} remaining students", allocated);
        return allocated;
    }

    private void allocateStudentToCourse(Student student, Course course) {
        // Update course enrolled count
        course.setEnrolledCount(course.getEnrolledCount() + 1);
        courseRepository.save(course);

        // Create selection record
        Selection selection = new Selection();
        selection.setStudent(student);
        selection.setCourse(course);
        selection.setSelectedAt(LocalDateTime.now());
        selection.setAutoAllocated(true);
        selectionRepository.save(selection);

        log.info("Allocated student {} to course {}", student.getStudentNo(), course.getName());
    }

    public static class AllocationResult {
        private final int totalUnselected;
        private final int phase1Allocated;
        private final int phase2Allocated;

        public AllocationResult(int totalUnselected, int phase1Allocated, int phase2Allocated) {
            this.totalUnselected = totalUnselected;
            this.phase1Allocated = phase1Allocated;
            this.phase2Allocated = phase2Allocated;
        }

        public int getTotalUnselected() { return totalUnselected; }
        public int getPhase1Allocated() { return phase1Allocated; }
        public int getPhase2Allocated() { return phase2Allocated; }
        public int getTotalAllocated() { return phase1Allocated + phase2Allocated; }
    }
}
