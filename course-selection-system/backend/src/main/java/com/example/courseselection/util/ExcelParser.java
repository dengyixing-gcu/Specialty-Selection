package com.example.courseselection.util;

import lombok.extern.slf4j.Slf4j;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

@Component
@Slf4j
public class ExcelParser {
    private static final int STUDENT_NO_COLUMN = 0;
    private static final int NAME_COLUMN = 1;

    public List<StudentInfo> parseStudentExcel(MultipartFile file) throws IOException {
        List<StudentInfo> students = new ArrayList<>();

        try (Workbook workbook = new XSSFWorkbook(file.getInputStream())) {
            Sheet sheet = workbook.getSheetAt(0);

            for (int rowIndex = 1; rowIndex <= sheet.getLastRowNum(); rowIndex++) {
                Row row = sheet.getRow(rowIndex);
                if (row == null) continue;

                String studentNo = getCellValue(row, STUDENT_NO_COLUMN);
                String name = getCellValue(row, NAME_COLUMN);

                if (studentNo != null && !studentNo.trim().isEmpty() &&
                    name != null && !name.trim().isEmpty()) {
                    students.add(new StudentInfo(studentNo.trim(), name.trim()));
                }
            }
        }

        log.info("Parsed {} students from Excel file", students.size());
        return students;
    }

    private String getCellValue(Row row, int columnIndex) {
        Cell cell = row.getCell(columnIndex);
        if (cell == null) return null;

        switch (cell.getCellType()) {
            case STRING:
                return cell.getStringCellValue();
            case NUMERIC:
                // Handle numeric student numbers
                double numValue = cell.getNumericCellValue();
                if (numValue == Math.floor(numValue) && !Double.isInfinite(numValue)) {
                    return String.valueOf((long) numValue);
                }
                return String.valueOf(numValue);
            default:
                return null;
        }
    }

    public static class StudentInfo {
        private final String studentNo;
        private final String name;

        public StudentInfo(String studentNo, String name) {
            this.studentNo = studentNo;
            this.name = name;
        }

        public String getStudentNo() {
            return studentNo;
        }

        public String getName() {
            return name;
        }
    }
}
