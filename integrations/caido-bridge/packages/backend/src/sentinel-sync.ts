/**
 * HTTP client for Sentinel API sync endpoints (no Caido SDK dependency).
 * Map Caido traffic to {@link SentinelRequest} / {@link SentinelFinding}.
 */

import type { SentinelFinding, SentinelRequest } from '../../shared/src/types';

export type SentinelBridgeConfig = {
  /** e.g. http://localhost:30880 (Compose default API port) */
  apiBaseUrl: string;
  /** Sentinel project UUID */
  projectId: string;
  /** Required when SENTINEL_REQUIRE_AUTH=true on the API */
  bearerToken?: string;
};

function normalizeBase(url: string): string {
  return url.replace(/\/$/, '');
}

export async function pushRequestsToSentinel(
  cfg: SentinelBridgeConfig,
  requests: SentinelRequest[],
): Promise<{ accepted: boolean; received: number }> {
  const base = normalizeBase(cfg.apiBaseUrl);
  const body = {
    project_id: cfg.projectId,
    requests: requests.map((r) => ({
      caido_request_id: r.caidoRequestId,
      method: r.method,
      url: r.url,
      host: r.host,
      path: r.path,
      status_code: r.statusCode,
      req_headers_json: r.reqHeaders ?? {},
      resp_headers_json: r.respHeaders ?? {},
    })),
  };
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (cfg.bearerToken) {
    headers.Authorization = `Bearer ${cfg.bearerToken}`;
  }
  const res = await fetch(`${base}/api/sync/requests`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Sentinel sync failed: ${res.status} ${text}`);
  }
  return (await res.json()) as { accepted: boolean; received: number };
}

function findingToApiItem(f: SentinelFinding) {
  const bugClass =
    f.title && f.bugClass ? `${f.bugClass}: ${f.title}` : f.bugClass || f.title || 'unspecified';
  return {
    source: f.source ?? 'caido',
    bug_class: bugClass,
    severity: f.severity,
    confidence: f.confidence,
  };
}

export async function pushFindingsToSentinel(
  cfg: SentinelBridgeConfig,
  findings: SentinelFinding[],
): Promise<{ accepted: boolean; received: number }> {
  const base = normalizeBase(cfg.apiBaseUrl);
  const body = {
    project_id: cfg.projectId,
    findings: findings.map(findingToApiItem),
  };
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (cfg.bearerToken) {
    headers.Authorization = `Bearer ${cfg.bearerToken}`;
  }
  const res = await fetch(`${base}/api/sync/findings`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Sentinel findings sync failed: ${res.status} ${text}`);
  }
  return (await res.json()) as { accepted: boolean; received: number };
}
