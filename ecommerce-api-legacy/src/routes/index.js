'use strict';

const express = require('express');

const { validate } = require('../middlewares/validate');
const { asyncHandler } = require('../middlewares/errorHandler');
const { checkoutSchema, normalizeCheckoutBody } = require('../schemas/checkoutSchema');
const { userIdParamSchema } = require('../schemas/userSchema');

/** Só mapeia rota → middleware de validação/autorização → controller. */
function buildRoutes({ checkoutController, reportController, userController, adminAuth }) {
    const router = express.Router();

    router.post(
        '/api/checkout',
        validate(checkoutSchema, { normalize: normalizeCheckoutBody }),
        asyncHandler(checkoutController.checkout),
    );

    router.get(
        '/api/admin/financial-report',
        adminAuth,
        asyncHandler(reportController.financialReport),
    );

    router.delete(
        '/api/users/:id',
        adminAuth,
        validate(userIdParamSchema, { source: 'params' }),
        asyncHandler(userController.remove),
    );

    return router;
}

module.exports = { buildRoutes };
