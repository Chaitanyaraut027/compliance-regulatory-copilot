'use strict';
require('dotenv').config();

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');

const config = require('./config');
const errorHandler = require('./middleware/errorHandler');

// Routes
const authRoutes = require('./routes/auth');
const complianceRoutes = require('./routes/compliance');
const uploadRoutes = require('./routes/upload');
const auditRoutes = require('./routes/audit');

const app = express();

// ── Global Middleware ─────────────────────────────────────────
app.use(helmet());                          // Security headers
app.use(cors());                            // CORS (allow all origins — restrict in production)
app.use(express.json({ limit: '1mb' }));   // Parse JSON body
app.use(express.urlencoded({ extended: true }));
app.use(morgan('dev'));                     // Request logging

// ── Health check (root) ───────────────────────────────────────
app.get('/', (req, res) => {
    res.json({
        service: 'Compliance Copilot — Node.js API Gateway',
        version: '1.0.0',
        status: 'running',
        endpoints: {
            auth: '/api/auth',
            compliance: '/api/compliance',
            upload: '/api/upload',
            audit: '/api/audit',
        },
    });
});

// ── API Routes ────────────────────────────────────────────────
app.use('/api/auth', authRoutes);
app.use('/api/compliance', complianceRoutes);
app.use('/api/upload', uploadRoutes);
app.use('/api/audit', auditRoutes);

// ── 404 handler ───────────────────────────────────────────────
app.use((req, res) => {
    res.status(404).json({ success: false, error: `Route not found: ${req.method} ${req.path}` });
});

// ── Global Error Handler (must be last) ───────────────────────
app.use(errorHandler);

// ── Start Server ──────────────────────────────────────────────
app.listen(config.port, () => {
    console.log(`\n🚀  Node.js API Gateway running on http://localhost:${config.port}`);
    console.log(`📡  Proxying AI requests to FastAPI at ${config.fastapiBaseUrl}\n`);
    console.log('Available routes:');
    console.log(`  POST   http://localhost:${config.port}/api/auth/register`);
    console.log(`  POST   http://localhost:${config.port}/api/auth/login`);
    console.log(`  GET    http://localhost:${config.port}/api/auth/me`);
    console.log(`  GET    http://localhost:${config.port}/api/compliance/health`);
    console.log(`  GET    http://localhost:${config.port}/api/compliance/documents`);
    console.log(`  POST   http://localhost:${config.port}/api/compliance/search`);
    console.log(`  POST   http://localhost:${config.port}/api/compliance/check`);
    console.log(`  POST   http://localhost:${config.port}/api/compliance/ingest  [admin]`);
    console.log(`  POST   http://localhost:${config.port}/api/upload/policy`);
    console.log(`  GET    http://localhost:${config.port}/api/upload/policies`);
    console.log(`  GET    http://localhost:${config.port}/api/audit`);
    console.log(`  GET    http://localhost:${config.port}/api/audit/:id`);
});

module.exports = app;
