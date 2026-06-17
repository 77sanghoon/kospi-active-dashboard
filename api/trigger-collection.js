const OWNER = process.env.GITHUB_OWNER || '77sanghoon';
const REPO = process.env.GITHUB_REPO || 'kospi-active-dashboard';
const WORKFLOW_ID = process.env.GITHUB_WORKFLOW_ID || 'kospi-active-daily.yml';
const REF = process.env.GITHUB_REF_NAME || 'main';
const ALLOWED_SLOTS = new Set(['0700', '0800', '0900', '1000']);

function json(res, statusCode, payload) {
  res.statusCode = statusCode;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.end(JSON.stringify(payload));
}

function requestUrl(req) {
  const host = req.headers.host || 'localhost';
  return new URL(req.url || '/', `https://${host}`);
}

function isAuthorized(req, url) {
  const secret = process.env.CRON_SECRET;
  if (!secret) return true;

  const auth = req.headers.authorization || '';
  const querySecret = url.searchParams.get('secret') || '';
  return auth === `Bearer ${secret}` || querySecret === secret;
}

module.exports = async function handler(req, res) {
  if (req.method !== 'GET' && req.method !== 'POST') {
    return json(res, 405, { ok: false, error: 'method_not_allowed' });
  }

  const url = requestUrl(req);
  if (!isAuthorized(req, url)) {
    return json(res, 401, { ok: false, error: 'unauthorized' });
  }

  const slot = url.searchParams.get('slot') || '';
  if (!ALLOWED_SLOTS.has(slot)) {
    return json(res, 400, { ok: false, error: 'invalid_slot', slot });
  }

  const token = process.env.GITHUB_ACTIONS_PAT || process.env.GH_ACTIONS_PAT || process.env.GITHUB_PAT;
  if (!token) {
    return json(res, 500, {
      ok: false,
      error: 'missing_github_token',
      message: 'Set GITHUB_ACTIONS_PAT in Vercel environment variables.',
    });
  }

  const endpoint = `https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW_ID}/dispatches`;
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'Content-Type': 'application/json',
      'User-Agent': 'kospi-active-vercel-cron',
      'X-GitHub-Api-Version': '2022-11-28',
    },
    body: JSON.stringify({
      ref: REF,
      inputs: {
        slot,
      },
    }),
  });

  if (!response.ok) {
    const detail = await response.text();
    return json(res, response.status, {
      ok: false,
      error: 'github_dispatch_failed',
      status: response.status,
      detail: detail.slice(0, 1000),
    });
  }

  return json(res, 202, {
    ok: true,
    slot,
    owner: OWNER,
    repo: REPO,
    workflow: WORKFLOW_ID,
    ref: REF,
  });
};
