#!/usr/bin/env node

const API_BASE = (process.env.SMOKE_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '');
const EMAIL = process.env.SMOKE_EMAIL || process.env.ADMIN_EMAIL || 'admin@example.com';
const PASSWORD = process.env.SMOKE_PASSWORD || process.env.ADMIN_PASSWORD || 'ReplaceWithStrongPassword123!';

function log(message) {
  process.stdout.write(`${message}\n`);
}

function fail(message) {
  throw new Error(message);
}

async function request(path, { method = 'GET', token, body } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  const text = await response.text();
  let data = null;

  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!response.ok) {
    const detail = typeof data === 'object' && data && 'detail' in data ? data.detail : data;
    fail(`${method} ${path} failed (${response.status}): ${String(detail ?? 'Unknown error')}`);
  }

  return data;
}

async function main() {
  log(`Using API base: ${API_BASE}`);
  log(`Authenticating as: ${EMAIL}`);

  const loginPayload = await request('/auth/login', {
    method: 'POST',
    body: { email: EMAIL, password: PASSWORD },
  });

  const token = loginPayload?.access_token;
  if (!token) {
    fail('Login succeeded but no access_token was returned.');
  }

  log('Login OK');

  await request('/auth/me', { token });
  await request('/topics', { token });
  await request('/drafts', { token });
  await request('/published', { token });
  await request('/audit?limit=5', { token });
  await request('/campaigns', { token });
  await request('/competitors', { token });
  await request('/hooks', { token });
  await request('/swipe-files', { token });
  await request('/performance', { token });
  await request('/performance/insights', { token });

  const campaign = await request('/campaigns', {
    method: 'POST',
    token,
    body: {
      title: `Smoke Campaign ${Date.now()}`,
      goal: 'lead generation',
      audience: 'founders',
      platforms: ['linkedin', 'twitter'],
      platform_entity: 'horizon',
    },
  });
  await request(`/campaigns/${campaign.id}/generate`, { method: 'POST', token });

  const competitor = await request('/competitors', {
    method: 'POST',
    token,
    body: {
      name: `Smoke Competitor ${Date.now()}`,
      platform: 'linkedin',
      profile_url: 'https://example.com/company/example',
      platform_entity: 'horizon',
    },
  });
  await request(`/competitors/${competitor.id}/analyze`, { method: 'POST', token });

  await request('/hooks/suggest?topic=ai%20growth&platform=linkedin&count=3', { token });

  await request('/daily-posts/generate', {
    method: 'POST',
    token,
    body: {
      industry: 'SaaS',
      region: 'usa',
      target_audience: 'founders',
      business_goal: 'leads',
    },
  });

  await request('/thought-leadership/generate', {
    method: 'POST',
    token,
    body: {
      topic: 'AI trust in B2B marketing',
      content_type: 'deep_insight',
      industry: 'SaaS',
    },
  });

  await request('/audience-content/generate', {
    method: 'POST',
    token,
    body: {
      audience_type: 'founders',
      region: 'global',
      income_bracket: 'middle',
      awareness_stage: 'warm',
      pain_points: ['low engagement', 'inconsistent leads'],
    },
  });

  await request('/platform-content/generate', {
    method: 'POST',
    token,
    body: {
      topic: 'AI product launch narrative',
      platform: 'linkedin',
      content_type: 'authority_post',
    },
  });

  await request('/repurpose', {
    method: 'POST',
    token,
    body: {
      content: 'Long source content for repurposing.',
      source_type: 'article',
      target_formats: ['linkedin_post', 'thread'],
    },
  });

  const swipe = await request('/swipe-files', {
    method: 'POST',
    token,
    body: {
      platform: 'linkedin',
      title: `Smoke Swipe ${Date.now()}`,
      content: 'Reusable high-performing content frame.',
      source_url: 'https://example.com/post',
      performance_notes: 'High save rate',
      tags: ['smoke', 'test'],
    },
  });
  await request(`/swipe-files/${swipe.id}`, { method: 'DELETE', token });

  log('API smoke run passed.');
}

main().catch((error) => {
  process.stderr.write(`Smoke run failed: ${error.message}\n`);
  process.exitCode = 1;
});
