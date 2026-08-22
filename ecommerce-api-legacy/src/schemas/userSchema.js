'use strict';

const { z } = require('zod');

const userIdParamSchema = z.object({
    id: z.coerce.number().int().positive(),
});

module.exports = { userIdParamSchema };
