'use strict';

const { PaymentStatus, UNKNOWN_STUDENT } = require('../config/constants');

/**
 * Monta o relatório financeiro a partir das linhas do JOIN.
 * A ordem é determinística (vem do `ORDER BY` da query), ao contrário do
 * código legado, que respondia na ordem de conclusão dos callbacks.
 */
function createReportService({ reportRepository }) {
    return {
        async financialReport({ limit, offset }) {
            const [rows, totalCourses] = await Promise.all([
                reportRepository.listCourseFinancials({ limit, offset }),
                reportRepository.countCourses(),
            ]);

            const byCourse = new Map();

            for (const row of rows) {
                if (!byCourse.has(row.course_id)) {
                    byCourse.set(row.course_id, {
                        course: row.course_title,
                        revenue: 0,
                        students: [],
                    });
                }

                if (row.enrollment_id === null) continue;

                const courseData = byCourse.get(row.course_id);

                if (row.payment_status === PaymentStatus.PAID) {
                    courseData.revenue += row.payment_amount;
                }

                courseData.students.push({
                    student: row.student_name ?? UNKNOWN_STUDENT,
                    paid: row.payment_amount ?? 0,
                });
            }

            return { report: [...byCourse.values()], totalCourses };
        },
    };
}

module.exports = { createReportService };
