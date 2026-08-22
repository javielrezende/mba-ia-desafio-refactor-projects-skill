'use strict';

/**
 * Erro de domínio: a mensagem é segura para ir na resposta HTTP.
 * Erros que não descendem daqui viram 500 genérico no error handler.
 */
class DomainError extends Error {
    constructor(message, statusCode = 400) {
        super(message);
        this.name = new.target.name;
        this.statusCode = statusCode;
        this.expose = true;
    }
}

class ValidationError extends DomainError {
    constructor(message = 'Bad Request', details = []) {
        super(message, 400);
        this.details = details;
    }
}

class NotFoundError extends DomainError {
    constructor(message = 'Não encontrado') {
        super(message, 404);
    }
}

class PaymentDeclinedError extends DomainError {
    constructor(message = 'Pagamento recusado') {
        super(message, 400);
    }
}

class UnauthorizedError extends DomainError {
    constructor(message = 'Não autorizado') {
        super(message, 401);
    }
}

module.exports = {
    DomainError,
    ValidationError,
    NotFoundError,
    PaymentDeclinedError,
    UnauthorizedError,
};
