'use strict';

const { z } = require('zod');
const { MIN_PASSWORD_LENGTH } = require('../config/constants');

/**
 * O payload público usa abreviações (`usr`, `eml`, `pwd`, `c_id`, `card`).
 * Renomeá-las seria breaking change, então os dois nomes são aceitos: os
 * antigos continuam funcionando e os novos ficam disponíveis para os clientes
 * migrarem (RP-15).
 */
function normalizeCheckoutBody(body = {}) {
    return {
        userName: body.userName ?? body.usr,
        email: body.email ?? body.eml,
        password: body.password ?? body.pwd,
        courseId: body.courseId ?? body.c_id,
        cardNumber: toStringOrPassthrough(body.cardNumber ?? body.card),
    };
}

function toStringOrPassthrough(value) {
    return typeof value === 'number' ? String(value) : value;
}

const checkoutSchema = z.object({
    userName: z.string().trim().min(1),
    email: z.email(),
    password: z.string().min(MIN_PASSWORD_LENGTH),
    courseId: z.coerce.number().int().positive(),
    cardNumber: z.string().regex(/^\d{13,19}$/),
});

module.exports = { checkoutSchema, normalizeCheckoutBody };
