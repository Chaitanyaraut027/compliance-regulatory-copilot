'use strict';
const express = require('express');
const { authenticate } = require('../middleware/auth');
const { query } = require('../db');

const router = express.Router();

// ── GET /api/audit ────────────────────────────────────────────
// Paginated list of the authenticated user's compliance checks
router.get('/', authenticate, async (req, res, next) => {
    try {
        const page = Math.max(1, parseInt(req.query.page || '1', 10));
        const limit = Math.min(50, Math.max(1, parseInt(req.query.limit || '20', 10)));
        const offset = (page - 1) * limit;

        const [dataResult, countResult] = await Promise.all([
            query(
                `SELECT id, question, compliance_area, overall_status, summary, created_at
           FROM audit_history
          WHERE user_id = $1
          ORDER BY created_at DESC
          LIMIT $2 OFFSET $3`,
                [req.user.id, limit, offset]
            ),
            query(
                `SELECT COUNT(*)::INT AS total FROM audit_history WHERE user_id = $1`,
                [req.user.id]
            ),
        ]);

        const total = countResult.rows[0].total;

        return res.json({
            success: true,
            data: dataResult.rows,
            pagination: {
                page,
                limit,
                total,
                totalPages: Math.ceil(total / limit),
            },
        });
    } catch (err) {
        next(err);
    }
});

// ── GET /api/audit/:id ────────────────────────────────────────
// Full detail of a single audit record (must belong to current user)
router.get('/:id', authenticate, async (req, res, next) => {
    try {
        const result = await query(
            `SELECT id, question, compliance_area, company_evidence, facility_description,
              overall_status, summary, findings, disclaimer, created_at
         FROM audit_history
        WHERE id = $1 AND user_id = $2`,
            [req.params.id, req.user.id]
        );

        if (result.rows.length === 0) {
            return res.status(404).json({ success: false, error: 'Audit record not found.' });
        }

        return res.json({ success: true, data: result.rows[0] });
    } catch (err) {
        next(err);
    }
});

module.exports = router;
