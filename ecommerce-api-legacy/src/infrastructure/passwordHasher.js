'use strict';

const crypto = require('node:crypto');

const KEY_LENGTH = 64;
const SALT_BYTES = 16;
const SCRYPT_COST = 16384;

/**
 * Hashing de senha com scrypt + salt aleatório por senha (RP-04).
 * Substitui o `badCrypto` — base64 concatenado, sem salt e determinístico.
 * Usa apenas o `crypto` nativo do Node: nenhuma dependência extra.
 */
function createPasswordHasher() {
    function derive(password, salt) {
        return new Promise((resolve, reject) => {
            crypto.scrypt(password, salt, KEY_LENGTH, { N: SCRYPT_COST }, (err, key) =>
                err ? reject(err) : resolve(key),
            );
        });
    }

    return {
        async hash(password) {
            const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
            const key = await derive(password, salt);
            return `scrypt$${salt}$${key.toString('hex')}`;
        },

        async verify(password, stored) {
            const [algorithm, salt, expected] = String(stored).split('$');
            if (algorithm !== 'scrypt' || !salt || !expected) return false;
            const key = await derive(password, salt);
            const expectedBuffer = Buffer.from(expected, 'hex');
            if (expectedBuffer.length !== key.length) return false;
            return crypto.timingSafeEqual(key, expectedBuffer);
        },
    };
}

module.exports = { createPasswordHasher };
