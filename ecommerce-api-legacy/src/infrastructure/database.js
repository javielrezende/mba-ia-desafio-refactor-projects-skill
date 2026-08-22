'use strict';

const sqlite3 = require('sqlite3');

/**
 * Abre a conexão e devolve a API promisificada.
 * Único ponto do projeto que conhece o driver — todo o resto recebe este
 * objeto por injeção (RP-06).
 */
function createDatabase({ file = ':memory:' } = {}) {
    const db = new sqlite3.Database(file);

    const api = {
        get(sql, params = []) {
            return new Promise((resolve, reject) => {
                db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
            });
        },

        all(sql, params = []) {
            return new Promise((resolve, reject) => {
                db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
            });
        },

        run(sql, params = []) {
            return new Promise((resolve, reject) => {
                db.run(sql, params, function onDone(err) {
                    if (err) return reject(err);
                    return resolve({ lastID: this.lastID, changes: this.changes });
                });
            });
        },

        exec(sql) {
            return new Promise((resolve, reject) => {
                db.exec(sql, (err) => (err ? reject(err) : resolve()));
            });
        },

        /**
         * Executa `work` dentro de uma transação: COMMIT no sucesso,
         * ROLLBACK em qualquer exceção (RP-09).
         */
        async transaction(work) {
            await api.run('BEGIN');
            try {
                const result = await work(api);
                await api.run('COMMIT');
                return result;
            } catch (err) {
                await api.run('ROLLBACK').catch(() => {});
                throw err;
            }
        },

        close() {
            return new Promise((resolve, reject) => {
                db.close((err) => (err ? reject(err) : resolve()));
            });
        },
    };

    return api;
}

module.exports = { createDatabase };
