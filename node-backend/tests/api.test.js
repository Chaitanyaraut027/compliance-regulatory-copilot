'use strict';
const http = require('http');

const BASE_URL = process.env.TEST_API_URL || 'http://localhost:3000';

function request(method, path, body = null, headers = {}) {
  return new Promise((resolve, reject) => {
    const url = new URL(`${BASE_URL}${path}`);
    const payload = body ? (typeof body === 'string' ? body : JSON.stringify(body)) : null;

    const requestHeaders = {
      'Content-Type': 'application/json',
      ...headers,
    };

    if (payload) {
      requestHeaders['Content-Length'] = Buffer.byteLength(payload);
    }

    const options = {
      method,
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + url.search,
      headers: requestHeaders,
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(data) });
        } catch {
          resolve({ status: res.statusCode, body: data });
        }
      });
    });

    req.on('error', reject);
    if (payload) {
      req.write(payload);
    }
    req.end();
  });
}

async function runTests() {
  console.log('🧪 Starting Node.js API Gateway Test Suite...\n');
  let passed = 0;
  let failed = 0;

  function assert(name, condition, extraInfo = '') {
    if (condition) {
      console.log(`  ✅ ${name}`);
      passed++;
    } else {
      console.error(`  ❌ ${name} ${extraInfo ? `— ${extraInfo}` : ''}`);
      failed++;
    }
  }

  try {
    // 1. Root health check
    const root = await request('GET', '/');
    assert('GET / returns 200', root.status === 200);
    assert('GET / identifies service', root.body?.service?.includes('Compliance Copilot'));

    // 2. Auth: Register unique user
    const testEmail = `test_${Date.now()}@example.com`;
    const regRes = await request('POST', '/api/auth/register', {
      name: 'Automated Tester',
      email: testEmail,
      password: 'password123',
    });
    assert('POST /api/auth/register returns 201', regRes.status === 201, `Got ${regRes.status}: ${JSON.stringify(regRes.body)}`);
    assert('Register returns JWT token', !!regRes.body?.token);

    // 3. Auth: Duplicate register fails with 409
    const dupRes = await request('POST', '/api/auth/register', {
      name: 'Duplicate',
      email: testEmail,
      password: 'password123',
    });
    assert('Duplicate register returns 409', dupRes.status === 409, `Got ${dupRes.status}`);

    // 4. Auth: Login
    const loginRes = await request('POST', '/api/auth/login', {
      email: testEmail,
      password: 'password123',
    });
    assert('POST /api/auth/login returns 200', loginRes.status === 200, `Got ${loginRes.status}`);
    const token = loginRes.body?.token;
    assert('Login returns JWT token', !!token);

    // 5. Auth: Protected /me without token fails with 401
    const unauthRes = await request('GET', '/api/auth/me');
    assert('GET /api/auth/me without token returns 401', unauthRes.status === 401);

    // 6. Auth: Protected /me with token succeeds
    const meRes = await request('GET', '/api/auth/me', null, {
      Authorization: `Bearer ${token}`,
    });
    assert('GET /api/auth/me with token returns 200', meRes.status === 200);
    assert('GET /api/auth/me returns user profile', meRes.body?.user?.email === testEmail);

    // 7. Validation: Invalid payload returns 400 with details
    const valRes = await request(
      'POST',
      '/api/compliance/search',
      { query: 'a' },
      { Authorization: `Bearer ${token}` }
    );
    assert('Validation failure returns 400', valRes.status === 400);
    assert('Validation failure includes details array', Array.isArray(valRes.body?.details));

    // 8. Compliance: Health check proxy to FastAPI
    const healthRes = await request('GET', '/api/compliance/health');
    assert('GET /api/compliance/health returns 200', healthRes.status === 200);
    assert('Compliance health proxies FastAPI status', healthRes.body?.data?.status === 'ok');

    // 9. Compliance: Search proxy to FastAPI
    const searchRes = await request(
      'POST',
      '/api/compliance/search',
      { query: 'licensing regulations', top_k: 2 },
      { Authorization: `Bearer ${token}` }
    );
    assert('POST /api/compliance/search returns 200', searchRes.status === 200, `Got ${searchRes.status}: ${JSON.stringify(searchRes.body)}`);
    assert('Search returns retrieved results', Array.isArray(searchRes.body?.data?.results));

    // 10. Audit History: List audits
    const auditRes = await request('GET', '/api/audit', null, {
      Authorization: `Bearer ${token}`,
    });
    assert('GET /api/audit returns 200', auditRes.status === 200);
    assert('Audit response has pagination', !!auditRes.body?.pagination);

    // 11. Policies: List uploaded policies
    const policyRes = await request('GET', '/api/upload/policies', null, {
      Authorization: `Bearer ${token}`,
    });
    assert('GET /api/upload/policies returns 200', policyRes.status === 200);
    assert('Policies response has data array', Array.isArray(policyRes.body?.data));

    // 12. 404 Route handling
    const notFoundRes = await request('GET', '/api/unknown_route');
    assert('Unknown route returns 404', notFoundRes.status === 404);

    console.log(`\n========================================`);
    console.log(`🏁 Test Summary: ${passed} passed, ${failed} failed`);
    console.log(`========================================\n`);

    if (failed > 0) {
      process.exit(1);
    }
  } catch (err) {
    console.error('Fatal test error:', err.message);
    process.exit(1);
  }
}

runTests();
