'use strict';
const { validationResult } = require('express-validator');

/**
 * Middleware that checks express-validator results.
 * If any validation errors exist, returns 400 with field-level details.
 * Place AFTER your validation chain:
 *   router.post('/route', [...validators], validate, handler)
 */
function validate(req, res, next) {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({
            success: false,
            error: 'Validation failed',
            details: errors.array().map((e) => ({
                field: e.path,
                message: e.msg,
                value: e.value,
            })),
        });
    }
    next();
}

module.exports = validate;
