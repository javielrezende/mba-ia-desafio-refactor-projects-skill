'use strict';

/** Status de pagamento aceitos pelo domínio. */
const PaymentStatus = Object.freeze({
    PAID: 'PAID',
    DENIED: 'DENIED',
});

/** Regra do gateway fake: cartão cujo BIN começa com este dígito é aprovado. */
const APPROVED_CARD_PREFIX = '4';

/** Número de dígitos do cartão mantidos em claro ao mascarar para log. */
const CARD_VISIBLE_DIGITS = 4;

/** Paginação da listagem do relatório financeiro. */
const DEFAULT_PAGE_SIZE = 20;
const MAX_PAGE_SIZE = 100;

/** Política de senha (RP-11). */
const MIN_PASSWORD_LENGTH = 8;

/** Rótulo usado quando a matrícula não tem usuário associado. */
const UNKNOWN_STUDENT = 'Unknown';

module.exports = {
    PaymentStatus,
    APPROVED_CARD_PREFIX,
    CARD_VISIBLE_DIGITS,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MIN_PASSWORD_LENGTH,
    UNKNOWN_STUDENT,
};
