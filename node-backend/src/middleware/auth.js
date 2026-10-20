'use strict';
const jwt = require('jsonwebtoken');
const config = require('../config');
const { query } = require('../db');

/**
 * JWT authentication middleware.
 * Expects: Authorization: Bearer <token>
 * On success: attaches req.user = { id, email, role, name }
 */
async function authenticate(req, res, next) {
    try {
        const authHeader = req.headers['authorization'];
        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return res.status(401).json({
                success: false,
                error: 'Access denied. No token provided. Use Authorization: Bearer <token>',
            });
        }

        const token = authHeader.slice(7);
        let payload;
        try {
            payload = jwt.verify(token, config.jwt.secret);
        } catch (err) {
            const msg = err.name === 'TokenExpiredError' ? 'Token has expired.' : 'Invalid token.';
            return res.status(401).json({ success: false, error: msg });
        }

        // Fetch fresh user from DB to ensure they still exist
        const result = await query(
            'SELECT id, name, email, role FROM users WHERE id = $1',
            [payload.id]
        );
        if (result.rows.length === 0) {
            return res.status(401).json({ success: false, error: 'User no longer exists.' });
        }

        req.user = result.rows[0];
        next();
    } catch (err) {
        next(err);
    }
}

/**
 * Role-based access middleware. Use after authenticate().
 * @param {string[]} roles - allowed roles, e.g. ['admin']
 */
function authorize(...roles) {
    return (req, res, next) => {
        if (!req.user || !roles.includes(req.user.role)) {
            return res.status(403).json({
                success: false,
                error: `Access forbidden. Required role: ${roles.join(' or ')}.`,
            });
        }
        next();
    };
}

module.exports = { authenticate, authorize };
