package com.example.courseselection.config;

import com.example.courseselection.service.AutoAllocationService;
import com.example.courseselection.service.SelectionService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
@Slf4j
public class AllocationScheduler {
    private final SelectionService selectionService;
    private final AutoAllocationService autoAllocationService;
    private boolean allocationExecuted = false;

    @Scheduled(fixedRate = 10000) // Check every 10 seconds
    public void checkAndExecuteAllocation() {
        if (allocationExecuted) {
            return;
        }

        // Check if selection period has ended
        if (!selectionService.isSelectionOpen()) {
            // Check if there was an open period that just ended
            if (selectionService.getSelectionOpenTime() != null) {
                log.info("Selection period has ended, executing auto allocation...");
                try {
                    AutoAllocationService.AllocationResult result = autoAllocationService.allocateUnselectedStudents();
                    log.info("Auto allocation completed: {}", result);
                    allocationExecuted = true;
                } catch (Exception e) {
                    log.error("Auto allocation failed", e);
                }
            }
        }
    }

    // Reset allocation flag when new selection period is set
    public void resetAllocationFlag() {
        allocationExecuted = false;
    }
}
