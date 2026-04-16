package com.example.courseselection.util;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;
import java.util.concurrent.TimeUnit;

@Component
@RequiredArgsConstructor
@Slf4j
public class RedisLockUtil {
    private final StringRedisTemplate redisTemplate;
    private static final String COURSE_LOCK_PREFIX = "lock:course:";
    private static final String STUDENT_LOCK_PREFIX = "lock:student:";
    private static final String RATE_LIMIT_PREFIX = "ratelimit:";
    private static final long LOCK_EXPIRE_TIME = 5; // 5 seconds
    private static final long RATE_LIMIT_WINDOW = 1; // 1 second

    public boolean tryLockCourse(Long courseId) {
        String key = COURSE_LOCK_PREFIX + courseId;
        return tryLock(key, LOCK_EXPIRE_TIME);
    }

    public void unlockCourse(Long courseId) {
        String key = COURSE_LOCK_PREFIX + courseId;
        unlock(key);
    }

    public boolean tryLockStudent(Long studentId) {
        String key = STUDENT_LOCK_PREFIX + studentId;
        return tryLock(key, LOCK_EXPIRE_TIME);
    }

    public void unlockStudent(Long studentId) {
        String key = STUDENT_LOCK_PREFIX + studentId;
        unlock(key);
    }

    public boolean tryRateLimit(String studentNo) {
        String key = RATE_LIMIT_PREFIX + studentNo;
        Boolean result = redisTemplate.opsForValue().setIfAbsent(key, "1", RATE_LIMIT_WINDOW, TimeUnit.SECONDS);
        return Boolean.TRUE.equals(result);
    }

    private boolean tryLock(String key, long expireTime) {
        Boolean result = redisTemplate.opsForValue().setIfAbsent(key, "locked", expireTime, TimeUnit.SECONDS);
        return Boolean.TRUE.equals(result);
    }

    private void unlock(String key) {
        redisTemplate.delete(key);
    }
}
