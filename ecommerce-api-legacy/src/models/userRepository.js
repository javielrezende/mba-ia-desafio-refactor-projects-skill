'use strict';

/**
 * Acesso a dados de `users`. Todas as queries são parametrizadas.
 * `toPublicJson` é o único serializador da entidade e nunca expõe o hash
 * da senha.
 */
function createUserRepository(db) {
    return {
        findByEmail(email) {
            return db.get('SELECT id, name, email FROM users WHERE email = ?', [email]);
        },

        findById(id) {
            return db.get('SELECT id, name, email FROM users WHERE id = ?', [id]);
        },

        async create({ name, email, passwordHash }, executor = db) {
            const { lastID } = await executor.run(
                'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
                [name, email, passwordHash],
            );
            return { id: lastID, name, email };
        },

        async deleteById(id) {
            const { changes } = await db.run('DELETE FROM users WHERE id = ?', [id]);
            return changes > 0;
        },

        toPublicJson(user) {
            return { id: user.id, name: user.name, email: user.email };
        },
    };
}

module.exports = { createUserRepository };
