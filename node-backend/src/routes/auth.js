'use strict';
const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { body } = require('express-validator');

const { query } = require('../db');
const config = require('../config');
const { authenticate } = require('../middleware/auth');
const validate = require('../middleware/validate');

const router = express.Router();

// ── Helper: sign JWT ──────────────────────────────────────────
function signToken(user) {
    return jwt.sign(
        { id: user.id, email: user.email, role: user.role },
        config.jwt.secret,
        { expiresIn: config.jwt.expiresIn }
    );
}

// ── POST /api/auth/register ───────────────────────────────────
router.post(
    '/register',
    [
        body('name').trim().notEmpty().withMessage('Name is required'),
        body('email').isEmail().normalizeEmail().withMessage('Valid email is required'),
        body('password')
            .isLength({ min: 8 })
            .withMessage('Password must be at least 8 characters'),
    ],
    validate,
    async (req, res, next) => {
        try {
            const { name, email, password } = req.body;

            // Check duplicate email
            const existing = await query('SELECT id FROM users WHERE email = $1', [email]);
            if (existing.rows.length > 0) {
                return res.status(409).json({ success: false, error: 'Email already registered.' });
            }

            const password_hash = await bcrypt.hash(password, 10);
            const result = await query(
                `INSERT INTO users (name, email, password_hash)
         VALUES ($1, $2, $3)
         RETURNING id, name, email, role, created_at`,
                [name, email, password_hash]
            );

            const user = result.rows[0];
            const token = signToken(user);

            return res.status(201).json({
                success: true,
                message: 'Registration successful.',
                token,
                user: { id: user.id, name: user.name, email: user.email, role: user.role },
            });
        } catch (err) {
            next(err);
        }
    }
);

// ── POST /api/auth/login ──────────────────────────────────────
router.post(
    '/login',
    [
        body('email').isEmail().normalizeEmail().withMessage('Valid email is required'),
        body('password').notEmpty().withMessage('Password is required'),
    ],
    validate,
    async (req, res, next) => {
        try {
            const { email, password } = req.body;

            const result = await query(
                'SELECT id, name, email, role, password_hash FROM users WHERE email = $1',
                [email]
            );
            if (result.rows.length === 0) {
                return res.status(401).json({ success: false, error: 'Invalid email or password.' });
            }

            const user = result.rows[0];
            const isMatch = await bcrypt.compare(password, user.password_hash);
            if (!isMatch) {
                return res.status(401).json({ success: false, error: 'Invalid email or password.' });
            }

            const token = signToken(user);

            return res.json({
                success: true,
                message: 'Login successful.',
                token,
                user: { id: user.id, name: user.name, email: user.email, role: user.role },
            });
        } catch (err) {
            next(err);
        }
    }
);

// ── GET /api/auth/me (protected) ──────────────────────────────
router.get('/me', authenticate, async (req, res, next) => {
    try {
        const result = await query(
            'SELECT id, name, email, role, created_at FROM users WHERE id = $1',
            [req.user.id]
        );
        if (result.rows.length === 0) {
            return res.status(404).json({ success: false, error: 'User not found.' });
        }
        return res.json({ success: true, user: result.rows[0] });
    } catch (err) {
        next(err);
    }
});

module.exports = router;
