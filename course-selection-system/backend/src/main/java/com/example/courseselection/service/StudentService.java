package com.example.courseselection.service;

import com.example.courseselection.entity.Student;
import com.example.courseselection.repository.StudentRepository;
import com.example.courseselection.util.ExcelParser;
import com.example.courseselection.util.PasswordGenerator;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
@Slf4j
public class StudentService {
    private final StudentRepository studentRepository;
    private final ExcelParser excelParser;
    private final PasswordGenerator passwordGenerator;
    private final PasswordEncoder passwordEncoder;

    @Transactional
    public ImportResult importStudents(MultipartFile file) throws IOException {
        List<ExcelParser.StudentInfo> studentInfos = excelParser.parseStudentExcel(file);
        List<Student> importedStudents = new ArrayList<>();
        List<String> skippedStudents = new ArrayList<>();
        List<String> passwords = new ArrayList<>();

        for (ExcelParser.StudentInfo info : studentInfos) {
            if (studentRepository.existsByStudentNo(info.getStudentNo())) {
                skippedStudents.add(info.getStudentNo());
                continue;
            }

            String rawPassword = passwordGenerator.generatePassword();
            String encodedPassword = passwordEncoder.encode(rawPassword);

            Student student = new Student();
            student.setStudentNo(info.getStudentNo());
            student.setName(info.getName());
            student.setPasswordHash(encodedPassword);
            student.setRole("STUDENT");

            studentRepository.save(student);
            importedStudents.add(student);
            passwords.add(rawPassword);

            log.info("Imported student: {} - {}", info.getStudentNo(), info.getName());
        }

        return new ImportResult(importedStudents.size(), skippedStudents.size(), skippedStudents, passwords);
    }

    public Student authenticate(String studentNo, String rawPassword) {
        Student student = studentRepository.findByStudentNo(studentNo)
                .orElse(null);

        if (student == null) {
            return null;
        }

        if (passwordEncoder.matches(rawPassword, student.getPasswordHash())) {
            return student;
        }

        return null;
    }

    public Student findByStudentNo(String studentNo) {
        return studentRepository.findByStudentNo(studentNo).orElse(null);
    }

    public List<Student> findAllStudents() {
        return studentRepository.findAll();
    }

    public static class ImportResult {
        private final int importedCount;
        private final int skippedCount;
        private final List<String> skippedStudentNos;
        private final List<String> passwords;

        public ImportResult(int importedCount, int skippedCount, List<String> skippedStudentNos, List<String> passwords) {
            this.importedCount = importedCount;
            this.skippedCount = skippedCount;
            this.skippedStudentNos = skippedStudentNos;
            this.passwords = passwords;
        }

        public int getImportedCount() { return importedCount; }
        public int getSkippedCount() { return skippedCount; }
        public List<String> getSkippedStudentNos() { return skippedStudentNos; }
        public List<String> getPasswords() { return passwords; }
    }
}
