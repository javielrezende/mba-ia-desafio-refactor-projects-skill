'use strict';

const { DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE } = require('../config/constants');

/**
 * Lê `page`/`per_page` da query string com teto, para que uma listagem não
 * possa mais varrer a tabela inteira (RP-16).
 */
function getPagination(query = {}) {
    const page = Math.max(1, toInteger(query.page, 1));
    const perPage = Math.min(MAX_PAGE_SIZE, Math.max(1, toInteger(query.per_page, DEFAULT_PAGE_SIZE)));
    return { page, perPage, limit: perPage, offset: (page - 1) * perPage };
}

function toInteger(value, fallback) {
    const parsed = Number.parseInt(value, 10);
    return Number.isNaN(parsed) ? fallback : parsed;
}

module.exports = { getPagination };
