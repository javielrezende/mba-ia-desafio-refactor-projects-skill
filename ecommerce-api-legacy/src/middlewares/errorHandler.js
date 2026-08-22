'use strict';

const { DomainError } = require('../domain/errors');

/**
 * Error handler central (RP-10): registrado por último, com 4 argumentos.
 * Erro de domínio vira o status e a mensagem que ele carrega; qualquer outro
 * vira 500 genérico, com o stack trace no log e nunca na resposta.
 */
function createErrorHandler({ logger }) {
    return function errorHandler(err, req, res, _next) {
        const isDomainError = err instanceof DomainError;
        const status = isDomainError ? err.statusCode : 500;

        logger[status >= 500 ? 'error' : 'warn'](
            { err, method: req.method, path: req.originalUrl, details: err.details },
            'requisição falhou',
        );

        res.status(status).send(isDomainError ? err.message : 'Erro interno');
    };
}

/** Encaminha rejeições de handlers async para o error handler (Express 4). */
function asyncHandler(handler) {
    return (req, res, next) => Promise.resolve(handler(req, res, next)).catch(next);
}

module.exports = { createErrorHandler, asyncHandler };
