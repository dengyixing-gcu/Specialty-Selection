package com.example.courseselection.entity;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import org.hibernate.annotations.UpdateTimestamp;
import java.time.LocalDateTime;

@Entity
@Table(name = "courses")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Course {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "name", nullable = false, length = 100)
    private String name;

    @Column(name = "capacity", nullable = false)
    private Integer capacity = 90;

    @Column(name = "enrolled_count", nullable = false)
    private Integer enrolledCount = 0;

    @Version
    @Column(name = "version")
    private Integer version = 0;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    public Integer getRemainingSlots() {
        return capacity - enrolledCount;
    }

    public boolean isFull() {
        return enrolledCount >= capacity;
    }
}
