'use strict';

/** Acesso a dados de `audit_logs`. */
function createAuditLogRepository(db) {
    return {
        create({ action }, executor = db) {
            return executor.run(
                "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
                [action],
            );
        },
    };
}

module.exports = { createAuditLogRepository };
