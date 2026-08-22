'use strict';

/** Acesso a dados de `payments`. */
function createPaymentRepository(db) {
    return {
        async create({ enrollmentId, amount, status }, executor = db) {
            const { lastID } = await executor.run(
                'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
                [enrollmentId, amount, status],
            );
            return { id: lastID, enrollmentId, amount, status };
        },
    };
}

module.exports = { createPaymentRepository };
