'use strict';

const crypto = require('node:crypto');
const { UnauthorizedError } = require('../domain/errors');

const API_KEY_HEADER = 'x-admin-api-key';

/**
 * Autorização das rotas administrativas.
 * No código legado o relatório financeiro e a remoção de usuários eram
 * públicos — qualquer um lia o faturamento e apagava contas.
 */
function createAdminAuth({ apiKey }) {
    if (!apiKey) throw new Error('adminAuth: apiKey é obrigatória');

    return function adminAuth(req, res, next) {
        const provided = req.get(API_KEY_HEADER);
        if (!provided || !safeEquals(provided, apiKey)) {
            return next(new UnauthorizedError());
        }
        return next();
    };
}

function safeEquals(a, b) {
    const bufferA = Buffer.from(a);
    const bufferB = Buffer.from(b);
    if (bufferA.length !== bufferB.length) return false;
    return crypto.timingSafeEqual(bufferA, bufferB);
}

module.exports = { createAdminAuth, API_KEY_HEADER };
