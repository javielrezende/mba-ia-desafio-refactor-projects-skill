'use strict';

/**
 * Consulta do relatório financeiro.
 * Substitui o laço `forEach` aninhado que disparava `1 + N + 2*(N*M)` queries
 * por uma única query com JOIN, paginada e com ordenação determinística (RP-08).
 */
function createReportRepository(db) {
    return {
        countCourses() {
            return db
                .get('SELECT COUNT(*) AS total FROM courses')
                .then(({ total }) => total);
        },

        listCourseFinancials({ limit, offset }) {
            return db.all(
                `WITH paged_courses AS (
                     SELECT id, title
                     FROM courses
                     ORDER BY id
                     LIMIT ? OFFSET ?
                 )
                 SELECT c.id        AS course_id,
                        c.title     AS course_title,
                        e.id        AS enrollment_id,
                        u.name      AS student_name,
                        p.amount    AS payment_amount,
                        p.status    AS payment_status
                 FROM paged_courses c
                 LEFT JOIN enrollments e ON e.course_id = c.id
                 LEFT JOIN users u       ON u.id = e.user_id
                 LEFT JOIN payments p    ON p.enrollment_id = e.id
                 ORDER BY c.id, e.id`,
                [limit, offset],
            );
        },
    };
}

module.exports = { createReportRepository };
