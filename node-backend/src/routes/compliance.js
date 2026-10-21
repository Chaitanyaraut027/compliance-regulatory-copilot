'use strict';
const express = require('express');
const { body } = require('express-validator');
const axios = require('axios');

const config = require('../config');
const { query } = require('../db');
const { authenticate, authorize } = require('../middleware/auth');
const validate = require('../middleware/validate');

const router = express.Router();

const FASTAPI = config.fastapiBaseUrl;
const PROXY_TIMEOUT = 60000; // 60s — compliance LLM calls can be slow
const COMPLIANCE_AREAS = [
    'General Labelling & Display',
    'Contaminants & Residues',
    'Food Additives',
    'Licensing & Registration',
    'Hygiene & Sanitary Practices',
];

// ── GET /api/compliance/health ────────────────────────────────
// Public — no auth needed
router.get('/health', async (req, res, next) => {
    try {
        const response = await axios.get(`${FASTAPI}/health`, { timeout: PROXY_TIMEOUT });
        return res.json({ success: true, data: response.data });
    } catch (err) {
        next(err);
    }
});

// ── GET /api/compliance/documents ────────────────────────────
router.get('/documents', authenticate, async (req, res, next) => {
    try {
        const response = await axios.get(`${FASTAPI}/documents`, { timeout: PROXY_TIMEOUT });
        return res.json({ success: true, data: response.data });
    } catch (err) {
        next(err);
    }
});

// ── POST /api/compliance/search ───────────────────────────────
router.post(
    '/search',
    authenticate,
    [
        body('query')
            .trim()
            .isLength({ min: 3 })
            .withMessage('Query must be at least 3 characters'),
        body('top_k')
            .optional()
            .isInt({ min: 1, max: 10 })
            .withMessage('top_k must be an integer between 1 and 10'),
    ],
    validate,
    async (req, res, next) => {
        try {
            const { query: searchQuery, top_k = 5 } = req.body;
            const response = await axios.post(
                `${FASTAPI}/search`,
                { query: searchQuery, top_k },
                { timeout: 30000 }
            );
            return res.json({ success: true, data: response.data });
        } catch (err) {
            next(err);
        }
    }
);

// ── POST /api/compliance/check ────────────────────────────────
router.post(
    '/check',
    authenticate,
    [
        body('question')
            .trim()
            .isLength({ min: 10 })
            .withMessage('Question must be at least 10 characters'),
        body('company_evidence')
            .trim()
            .isLength({ min: 20 })
            .withMessage('Company evidence must be at least 20 characters'),
        body('compliance_area')
            .trim()
            .notEmpty()
            .isIn(COMPLIANCE_AREAS)
            .withMessage(`compliance_area must be one of: ${COMPLIANCE_AREAS.join(', ')}`),
        body('facility_description').optional().trim(),
        body('top_k')
            .optional()
            .isInt({ min: 1, max: 10 })
            .withMessage('top_k must be between 1 and 10'),
    ],
    validate,
    async (req, res, next) => {
        try {
            const {
                question,
                company_evidence,
                compliance_area,
                facility_description,
                product_name,
                product_id,
                top_k = 5,
            } = req.body;

            // Proxy to FastAPI
            const response = await axios.post(
                `${FASTAPI}/compliance/check`,
                { question, company_evidence, compliance_area, facility_description, top_k },
                { timeout: 90000 }
            );

            const result = response.data;

            // Persist audit record for the logged-in user
            const auditInsert = await query(
                `INSERT INTO audit_history
           (user_id, question, compliance_area, company_evidence, facility_description,
            overall_status, summary, findings, disclaimer, product_name, product_id)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
         RETURNING id, created_at`,
                [
                    req.user.id,
                    question,
                    compliance_area,
                    company_evidence,
                    facility_description || null,
                    result.overall_status || null,
                    result.summary || null,
                    JSON.stringify(result.findings || []),
                    result.disclaimer || null,
                    product_name || null,
                    product_id || null,
                ]
            );
            if (auditInsert.rows && auditInsert.rows[0]) {
                result.audit_id = auditInsert.rows[0].id;
                result.created_at = auditInsert.rows[0].created_at;
            }
            result.product_name = product_name || null;

            return res.json({ success: true, data: result });
        } catch (err) {
            next(err);
        }
    }
);

// ── POST /api/compliance/ingest (admin only) ──────────────────
router.post('/ingest', authenticate, authorize('admin'), async (req, res, next) => {
    try {
        const response = await axios.post(`${FASTAPI}/ingest`, req.body || {}, {
            timeout: 300000,
        });
        return res.json({ success: true, data: response.data });
    } catch (err) {
        next(err);
    }
});

module.exports = router;
