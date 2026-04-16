package com.example.courseselection;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class CourseSelectionApplication {
    public static void main(String[] args) {
        SpringApplication.run(CourseSelectionApplication.class, args);
    }
}
