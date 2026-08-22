'use strict';

const config = require('./config');
const { buildApp } = require('./app');

async function main() {
    const { app, db, logger } = await buildApp();

    if (config.missingSecrets.length > 0) {
        logger.warn(
            { variables: config.missingSecrets },
            'variáveis sensíveis ausentes: usando valores de desenvolvimento (ver .env.example)',
        );
    }

    const server = app.listen(config.port, () => {
        logger.info({ port: config.port, env: config.env }, 'LMS API no ar');
    });

    for (const signal of ['SIGINT', 'SIGTERM']) {
        process.once(signal, () => {
            logger.info({ signal }, 'encerrando');
            server.close(() => db.close().finally(() => process.exit(0)));
        });
    }
}

main().catch((err) => {
    process.stderr.write(`${err.stack}\n`);
    process.exit(1);
});
