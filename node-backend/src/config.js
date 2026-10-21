'use strict';
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });
require('dotenv').config();

const config = {
  port: parseInt(process.env.PORT || '3000', 10),
  fastapiBaseUrl: process.env.FASTAPI_BASE_URL || 'http://localhost:8000',
  databaseUrl: process.env.DATABASE_URL,
  jwt: {
    secret: process.env.JWT_SECRET || 'changeme',
    expiresIn: process.env.JWT_EXPIRES_IN || '7d',
  },
  upload: {
    maxFileSizeMb: parseInt(process.env.MAX_FILE_SIZE_MB || '5', 10),
    dir: process.env.UPLOAD_DIR || 'uploads/',
  },
  isDev: process.env.NODE_ENV !== 'production',
};

if (!config.databaseUrl) {
  console.error('FATAL: DATABASE_URL is not set in .env');
  process.exit(1);
}

if (!process.env.JWT_SECRET) {
  console.warn('WARNING: JWT_SECRET not set — using insecure default. Set it in .env!');
}

module.exports = config;
