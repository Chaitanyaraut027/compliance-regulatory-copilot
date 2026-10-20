'use strict';
const express = require('express');
const multer = require('multer');
const pdfParse = require('pdf-parse');

const { query } = require('../db');
const { authenticate } = require('../middleware/auth');
const config = require('../config');

const router = express.Router();

// Use memory storage — buffer passed directly to pdf-parse, no disk I/O needed
const upload = multer({
    storage: multer.memoryStorage(),
    limits: { fileSize: config.upload.maxFileSizeMb * 1024 * 1024 },
    fileFilter: (_req, file, cb) => {
        if (file.mimetype !== 'application/pdf') {
            return cb(new Error('Only PDF files are allowed. Received: ' + file.mimetype));
        }
        cb(null, true);
    },
});

// ── POST /api/upload/policy ────────────────────────────────────
router.post('/policy', authenticate, upload.single('file'), async (req, res, next) => {
    try {
        if (!req.file) {
            return res.status(400).json({ success: false, error: 'No PDF file uploaded. Use field name: file' });
        }

        // Extract text from in-memory buffer
        let pdfData;
        try {
            pdfData = await pdfParse(req.file.buffer);
        } catch (parseErr) {
            return res.status(422).json({
                success: false,
                error: 'Could not extract text from PDF. Ensure the PDF is text-based (not a scanned image).',
            });
        }

        const extracted_text = pdfData.text.trim();
        const char_count = extracted_text.length;

        // Save to DB
        const result = await query(
            `INSERT INTO company_policy_docs (user_id, filename, extracted_text, char_count)
       VALUES ($1, $2, $3, $4)
       RETURNING id, filename, char_count, created_at`,
            [req.user.id, req.file.originalname, extracted_text, char_count]
        );

        return res.status(201).json({
            success: true,
            message: 'PDF uploaded and text extracted successfully.',
            document: result.rows[0],
            extracted_text,
            char_count,
        });
    } catch (err) {
        next(err);
    }
});

// ── GET /api/upload/policies ─────────────────────────────────
router.get('/policies', authenticate, async (req, res, next) => {
    try {
        const result = await query(
            `SELECT id, filename, char_count, created_at
         FROM company_policy_docs
        WHERE user_id = $1
        ORDER BY created_at DESC`,
            [req.user.id]
        );
        return res.json({ success: true, data: result.rows });
    } catch (err) {
        next(err);
    }
});

// ── GET /api/upload/policies/:id ─────────────────────────────
router.get('/policies/:id', authenticate, async (req, res, next) => {
    try {
        const result = await query(
            `SELECT id, filename, extracted_text, char_count, created_at
         FROM company_policy_docs
        WHERE id = $1 AND user_id = $2`,
            [req.params.id, req.user.id]
        );
        if (result.rows.length === 0) {
            return res.status(404).json({ success: false, error: 'Policy document not found.' });
        }
        return res.json({ success: true, data: result.rows[0] });
    } catch (err) {
        next(err);
    }
});

// Handle multer errors (file size, wrong type)
router.use((err, req, res, next) => {
    if (err instanceof multer.MulterError || (err.message && err.message.includes('PDF'))) {
        return res.status(400).json({ success: false, error: err.message });
    }
    next(err);
});

module.exports = router;
