package com.example.courseselection.entity;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import java.time.LocalDateTime;

@Entity
@Table(name = "selections", uniqueConstraints = {
    @UniqueConstraint(columnNames = {"student_id"})
})
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Selection {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "student_id", nullable = false)
    private Student student;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "course_id", nullable = false)
    private Course course;

    @Column(name = "selected_at", nullable = false)
    private LocalDateTime selectedAt;

    @Column(name = "is_auto_allocated", nullable = false)
    private Boolean isAutoAllocated = false;

    @PrePersist
    protected void onCreate() {
        if (selectedAt == null) {
            selectedAt = LocalDateTime.now();
        }
    }
}
