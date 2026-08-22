'use strict';

const { ValidationError } = require('../domain/errors');

/**
 * Valida uma parte do request contra um schema e guarda o resultado em
 * `req.validated`. O corpo de erro devolvido continua sendo `Bad Request`,
 * como no contrato original — o detalhe do que falhou vai para o log, não
 * para a resposta.
 */
function validate(schema, { source = 'body', normalize } = {}) {
    return function validateMiddleware(req, res, next) {
        const raw = normalize ? normalize(req[source]) : req[source];
        const result = schema.safeParse(raw);

        if (!result.success) {
            return next(
                new ValidationError(
                    'Bad Request',
                    result.error.issues.map((issue) => ({
                        field: issue.path.join('.'),
                        message: issue.message,
                    })),
                ),
            );
        }

        req.validated = { ...req.validated, ...result.data };
        return next();
    };
}

module.exports = { validate };
