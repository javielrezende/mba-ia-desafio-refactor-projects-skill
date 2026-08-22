'use strict';

/** Acesso a dados de `enrollments`. */
function createEnrollmentRepository(db) {
    return {
        async create({ userId, courseId }, executor = db) {
            const { lastID } = await executor.run(
                'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
                [userId, courseId],
            );
            return { id: lastID, userId, courseId };
        },
    };
}

module.exports = { createEnrollmentRepository };
