package com.example.courseselection.repository;

import com.example.courseselection.entity.Student;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;

@Repository
public interface StudentRepository extends JpaRepository<Student, Long> {
    Optional<Student> findByStudentNo(String studentNo);
    boolean existsByStudentNo(String studentNo);
    List<Student> findAllByStudentNoIn(List<String> studentNos);
}
