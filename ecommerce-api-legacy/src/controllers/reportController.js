'use strict';

const { getPagination } = require('../middlewares/pagination');

/**
 * O corpo continua sendo o array puro do contrato original; a paginação vai
 * em headers, para não quebrar quem já consome a resposta.
 */
function createReportController({ reportService }) {
    return {
        async financialReport(req, res) {
            const { page, perPage, limit, offset } = getPagination(req.query);
            const { report, totalCourses } = await reportService.financialReport({ limit, offset });

            res.set('X-Total-Count', String(totalCourses));
            res.set('X-Page', String(page));
            res.set('X-Per-Page', String(perPage));
            res.status(200).json(report);
        },
    };
}

module.exports = { createReportController };
