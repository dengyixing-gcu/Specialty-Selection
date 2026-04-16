package com.example.courseselection.controller;

import com.example.courseselection.entity.Student;
import com.example.courseselection.service.StudentService;
import com.example.courseselection.util.JwtUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {
    private final StudentService studentService;
    private final JwtUtil jwtUtil;

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody LoginRequest request) {
        Student student = studentService.authenticate(request.getStudentNo(), request.getPassword());

        if (student == null) {
            return ResponseEntity.badRequest().body(Map.of("message", "学号或密码错误"));
        }

        String token = jwtUtil.generateToken(student.getStudentNo(), student.getRole());

        return ResponseEntity.ok(Map.of(
            "token", token,
            "user", Map.of(
                "studentNo", student.getStudentNo(),
                "name", student.getName(),
                "role", student.getRole()
            )
        ));
    }

    @PostMapping("/admin/login")
    public ResponseEntity<?> adminLogin(@RequestBody AdminLoginRequest request) {
        // Simple admin authentication - in production, use proper admin credentials
        if ("admin".equals(request.getUsername()) && "admin123".equals(request.getPassword())) {
            String token = jwtUtil.generateToken("admin", "ADMIN");
            return ResponseEntity.ok(Map.of(
                "token", token,
                "user", Map.of(
                    "username", "admin",
                    "role", "ADMIN"
                )
            ));
        }

        return ResponseEntity.badRequest().body(Map.of("message", "管理员账号或密码错误"));
    }

    public static class LoginRequest {
        private String studentNo;
        private String password;

        public String getStudentNo() { return studentNo; }
        public void setStudentNo(String studentNo) { this.studentNo = studentNo; }
        public String getPassword() { return password; }
        public void setPassword(String password) { this.password = password; }
    }

    public static class AdminLoginRequest {
        private String username;
        private String password;

        public String getUsername() { return username; }
        public void setUsername(String username) { this.username = username; }
        public String getPassword() { return password; }
        public void setPassword(String password) { this.password = password; }
    }
}
