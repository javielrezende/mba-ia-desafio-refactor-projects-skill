'use strict';

const { PaymentStatus, APPROVED_CARD_PREFIX, CARD_VISIBLE_DIGITS } = require('../config/constants');

/** Mantém apenas os últimos dígitos do cartão — nunca logue o PAN completo. */
function maskCard(cardNumber) {
    const digits = String(cardNumber);
    return `**** **** **** ${digits.slice(-CARD_VISIBLE_DIGITS)}`;
}

/**
 * Gateway de pagamento fake, com a mesma regra de aprovação do código legado
 * (cartão iniciado em "4" é aprovado), agora atrás de uma interface injetável.
 * A chave da API fica no gateway e nunca é logada nem devolvida.
 */
function createFakePaymentGateway({ apiKey, logger }) {
    if (!apiKey) throw new Error('paymentGateway: apiKey é obrigatória');

    return {
        async charge({ cardNumber, amount }) {
            const status = String(cardNumber).startsWith(APPROVED_CARD_PREFIX)
                ? PaymentStatus.PAID
                : PaymentStatus.DENIED;

            logger.info({ card: maskCard(cardNumber), amount, status }, 'cobrança processada');
            return { status, amount };
        },
    };
}

module.exports = { createFakePaymentGateway, maskCard };
