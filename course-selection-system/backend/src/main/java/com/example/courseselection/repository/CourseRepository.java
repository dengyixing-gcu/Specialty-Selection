package com.example.courseselection.repository;

import com.example.courseselection.entity.Course;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;
import jakarta.persistence.LockModeType;
import java.util.List;
import java.util.Optional;

@Repository
public interface CourseRepository extends JpaRepository<Course, Long> {
    List<Course> findAllByOrderByEnrolledCountAsc();

    @Query("SELECT c FROM Course c WHERE c.enrolledCount < c.capacity ORDER BY c.enrolledCount ASC")
    List<Course> findAvailableCourses();

    @Query("SELECT c FROM Course c WHERE c.enrolledCount < 30 ORDER BY c.enrolledCount ASC")
    List<Course> findCoursesWithLowEnrollment();

    @Lock(LockModeType.OPTIMISTIC)
    Optional<Course> findById(Long id);
}
