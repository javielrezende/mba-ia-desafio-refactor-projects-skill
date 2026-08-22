'use strict';

const express = require('express');

const config = require('./config');
const { createLogger } = require('./infrastructure/logger');
const { createDatabase } = require('./infrastructure/database');
const { migrate } = require('./infrastructure/migrations');
const { createPasswordHasher } = require('./infrastructure/passwordHasher');
const { createFakePaymentGateway } = require('./infrastructure/paymentGateway');

const { createUserRepository } = require('./models/userRepository');
const { createCourseRepository } = require('./models/courseRepository');
const { createEnrollmentRepository } = require('./models/enrollmentRepository');
const { createPaymentRepository } = require('./models/paymentRepository');
const { createAuditLogRepository } = require('./models/auditLogRepository');
const { createReportRepository } = require('./models/reportRepository');

const { createCheckoutService } = require('./services/checkoutService');
const { createReportService } = require('./services/reportService');
const { createUserService } = require('./services/userService');

const { createCheckoutController } = require('./controllers/checkoutController');
const { createReportController } = require('./controllers/reportController');
const { createUserController } = require('./controllers/userController');

const { buildRoutes } = require('./routes');
const { createAdminAuth } = require('./middlewares/adminAuth');
const { createErrorHandler } = require('./middlewares/errorHandler');

/**
 * Composition root: único lugar do projeto que constrói dependências concretas
 * e as injeta nas camadas. Passando `db`, `logger` ou `paymentGateway` dá para
 * montar a aplicação inteira com dublês, sem banco nem gateway reais.
 */
async function buildApp({
    logger = createLogger({ level: config.logLevel }),
    db = createDatabase({ file: config.databaseFile }),
    passwordHasher = createPasswordHasher(),
    paymentGateway = null,
    runMigrations = true,
} = {}) {
    const gateway =
        paymentGateway ??
        createFakePaymentGateway({ apiKey: config.paymentGatewayKey, logger });

    if (runMigrations) {
        await migrate(db, { passwordHasher });
    }

    const userRepository = createUserRepository(db);
    const courseRepository = createCourseRepository(db);
    const enrollmentRepository = createEnrollmentRepository(db);
    const paymentRepository = createPaymentRepository(db);
    const auditLogRepository = createAuditLogRepository(db);
    const reportRepository = createReportRepository(db);

    const checkoutService = createCheckoutService({
        db,
        userRepository,
        courseRepository,
        enrollmentRepository,
        paymentRepository,
        auditLogRepository,
        paymentGateway: gateway,
        passwordHasher,
        logger,
    });
    const reportService = createReportService({ reportRepository });
    const userService = createUserService({ userRepository, auditLogRepository, logger });

    const app = express();
    app.use(express.json());

    app.use(
        buildRoutes({
            checkoutController: createCheckoutController({ checkoutService }),
            reportController: createReportController({ reportService }),
            userController: createUserController({ userService }),
            adminAuth: createAdminAuth({ apiKey: config.adminApiKey }),
        }),
    );

    app.use(createErrorHandler({ logger }));

    return { app, db, logger };
}

module.exports = { buildApp };
