'use strict';

/**
 * Regra de negócio de usuários.
 * A remoção em cascata é garantida pelas FOREIGN KEY do schema somadas ao
 * `PRAGMA foreign_keys = ON` — matrículas e pagamentos do usuário deixam de
 * ficar órfãos, como acontecia no código legado.
 */
function createUserService({ userRepository, auditLogRepository, logger }) {
    return {
        async deleteUser(userId) {
            const deleted = await userRepository.deleteById(userId);
            await auditLogRepository.create({ action: `Remoção do usuário ${userId}` });
            logger.info({ userId, deleted }, 'usuário removido');
            return deleted;
        },
    };
}

module.exports = { createUserService };
