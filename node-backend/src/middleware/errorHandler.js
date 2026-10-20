'use strict';
const config = require('../config');

/**
 * Global error handler middleware.
 * Must be registered last: app.use(errorHandler)
 */
function errorHandler(err, req, res, _next) {
    if (config.isDev) {
        console.error('[ERROR]', err.stack || err.message);
    }

    // Axios errors from FastAPI proxy
    if (err.isAxiosError) {
        const status = err.response?.status || 502;
        const detail = err.response?.data?.detail || err.message;
        return res.status(status).json({
            success: false,
            error: `FastAPI error: ${detail}`,
        });
    }

    const status = err.status || err.statusCode || 500;
    const message = err.message || 'Internal server error';

    return res.status(status).json({ success: false, error: message });
}

module.exports = errorHandler;
