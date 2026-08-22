'use strict';

/** Acesso a dados de `courses`. */
function createCourseRepository(db) {
    return {
        findActiveById(id) {
            return db.get('SELECT id, title, price FROM courses WHERE id = ? AND active = 1', [id]);
        },

        async countAll() {
            const { total } = await db.get('SELECT COUNT(*) AS total FROM courses');
            return total;
        },
    };
}

module.exports = { createCourseRepository };
