package com.example.courseselection.repository;

import com.example.courseselection.entity.Selection;
import com.example.courseselection.entity.Student;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;

@Repository
public interface SelectionRepository extends JpaRepository<Selection, Long> {
    Optional<Selection> findByStudent(Student student);
    Optional<Selection> findByStudentId(Long studentId);
    boolean existsByStudentId(Long studentId);
    List<Selection> findAllByIsAutoAllocatedFalse();

    @Query("SELECT s.student.id FROM Selection s")
    List<Long> findAllSelectedStudentIds();

    @Query("SELECT s FROM Selection s JOIN FETCH s.course WHERE s.student.id = :studentId")
    Optional<Selection> findByStudentIdWithCourse(Long studentId);
}
