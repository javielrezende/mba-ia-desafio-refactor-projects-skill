'use strict';

require('dotenv').config({ quiet: true });

const isProduction = process.env.NODE_ENV === 'production';

/**
 * Lê uma variável de ambiente sensível.
 * Em produção a ausência derruba o boot — melhor não subir do que subir com
 * segredo default. Fora de produção usa o valor de desenvolvimento e avisa,
 * para que `npm start` continue funcionando sem `.env`.
 */
function secret(name, developmentFallback) {
    const value = process.env[name];
    if (value) return value;

    if (isProduction) {
        throw new Error(`Variável de ambiente obrigatória ausente: ${name}`);
    }
    missingSecrets.push(name);
    return developmentFallback;
}

const missingSecrets = [];

const config = {
    env: process.env.NODE_ENV || 'development',
    port: Number(process.env.PORT || 3000),
    logLevel: process.env.LOG_LEVEL || 'info',
    databaseFile: process.env.DATABASE_FILE || ':memory:',
    paymentGatewayKey: secret('PAYMENT_GATEWAY_KEY', 'dev-payment-key-not-a-real-secret'),
    adminApiKey: secret('ADMIN_API_KEY', 'dev-admin-key-not-a-real-secret'),
    /** Nomes das variáveis que caíram no fallback de desenvolvimento. */
    missingSecrets,
};

module.exports = config;
