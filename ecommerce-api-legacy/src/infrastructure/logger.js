'use strict';

const LEVELS = { debug: 10, info: 20, warn: 30, error: 40 };

/**
 * Logger estruturado com nível, timestamp e destino único (stdout).
 * Substitui o `console.log` espalhado pelo código legado.
 */
function createLogger({ level = 'info', stream = process.stdout } = {}) {
    const threshold = LEVELS[level] ?? LEVELS.info;

    function write(levelName, context, message) {
        if (LEVELS[levelName] < threshold) return;
        const entry = {
            time: new Date().toISOString(),
            level: levelName,
            msg: message,
            ...serializeContext(context),
        };
        stream.write(`${JSON.stringify(entry)}\n`);
    }

    return {
        debug: (context, message) => write('debug', context, message),
        info: (context, message) => write('info', context, message),
        warn: (context, message) => write('warn', context, message),
        error: (context, message) => write('error', context, message),
    };
}

function serializeContext(context) {
    if (!context) return {};
    if (context instanceof Error) return { err: errorToJson(context) };
    const { err, ...rest } = context;
    return err instanceof Error ? { ...rest, err: errorToJson(err) } : context;
}

function errorToJson(err) {
    return { name: err.name, message: err.message, stack: err.stack };
}

module.exports = { createLogger };
