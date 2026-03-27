import Link from 'next/link';

import { getApiBaseUrl } from '../../lib/api-base';

type VersionPayload = {
  version: string;
  service: string;
  writes_disabled?: boolean;
  rate_limit_rpm?: number;
};

type McpPayload = {
  loaded: boolean;
  path_configured: boolean;
  error: string | null;
  server_count: number;
  suppressed_server_count?: number;
  servers: { name: string; transport: string }[];
};

export default async function AdminPage() {
  const base = getApiBaseUrl();
  let health = 'unknown';
  let version: VersionPayload | null = null;
  let mcp: McpPayload | null = null;
  let err: string | null = null;

  try {
    const [h, v, m] = await Promise.all([
      fetch(`${base}/health`, { cache: 'no-store' }),
      fetch(`${base}/api/version`, { cache: 'no-store' }),
      fetch(`${base}/api/mcp/servers`, { cache: 'no-store' }),
    ]);
    if (h.ok) {
      const hj = (await h.json()) as { status?: string };
      health = hj.status ?? 'ok';
    }
    if (v.ok) {
      version = (await v.json()) as VersionPayload;
    }
    if (m.ok) {
      mcp = (await m.json()) as McpPayload;
    }
    if (!v.ok || !m.ok) {
      err = 'Some API calls failed (check auth and base URL).';
    }
  } catch {
    err = 'API unreachable';
  }

  return (
    <main style={{ fontFamily: 'system-ui, sans-serif', padding: 32, maxWidth: 720 }}>
      <p>
        <Link href="/">← Home</Link>
      </p>
      <h1>Policy & operations</h1>
      <p style={{ color: '#555', marginTop: 0 }}>
        Read-only view of API flags useful for analysts and admins. Authoritative policy text lives in{' '}
        <strong>docs/architecture.md</strong> (MCP allowlist model) and <strong>PLAN.md</strong>.
      </p>
      {err ? <p style={{ color: '#a30' }}>{err}</p> : null}

      <section style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: '1.05rem' }}>Live status</h2>
        <ul>
          <li>
            Health: <strong>{health}</strong>
          </li>
          {version ? (
            <>
              <li>
                API: <strong>{version.version}</strong> ({version.service})
              </li>
              <li>
                Writes disabled (kill-switch):{' '}
                <strong>{version.writes_disabled ? 'yes' : 'no'}</strong> (
                <code>SENTINEL_API_WRITES_DISABLED</code>)
              </li>
              <li>
                Rate limit:{' '}
                <strong>
                  {version.rate_limit_rpm && version.rate_limit_rpm > 0
                    ? `${version.rate_limit_rpm} RPM on /api/*`
                    : 'off'}
                </strong>{' '}
                (<code>SENTINEL_RATE_LIMIT_RPM</code>)
              </li>
            </>
          ) : null}
        </ul>
      </section>

      <section style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: '1.05rem' }}>MCP summary</h2>
        {!mcp ? (
          <p style={{ color: '#666' }}>Could not load MCP status.</p>
        ) : (
          <ul>
            <li>
              Config path set: <strong>{mcp.path_configured ? 'yes' : 'no'}</strong>
            </li>
            <li>
              Loaded: <strong>{mcp.loaded ? 'yes' : 'no'}</strong>
              {mcp.error ? <span style={{ color: '#a30' }}> ({mcp.error})</span> : null}
            </li>
            <li>
              Servers listed: <strong>{mcp.server_count}</strong>
              {(mcp.suppressed_server_count ?? 0) > 0 ? (
                <span>
                  {' '}
                  (<strong>{mcp.suppressed_server_count}</strong> hidden via{' '}
                  <code>SENTINEL_MCP_DISABLED_SERVERS</code>)
                </span>
              ) : null}
            </li>
          </ul>
        )}
        {mcp && mcp.servers.length > 0 ? (
          <ul style={{ fontSize: 14 }}>
            {mcp.servers.map((s) => (
              <li key={s.name}>
                {s.name} — <code>{s.transport}</code>
              </li>
            ))}
          </ul>
        ) : null}
      </section>

      <section style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: '1.05rem' }}>Scope & mutating routes</h2>
        <p style={{ fontSize: 14, color: '#444', lineHeight: 1.5 }}>
          Projects carry a <strong>scope manifest</strong> (allowed hosts). Mutating sync and hypothesis
          routes check scope before writes. JWT auth is optional via <code>SENTINEL_REQUIRE_AUTH</code> /{' '}
          <code>SENTINEL_JWT_SECRET</code> (see README).
        </p>
      </section>

      <section>
        <h2 style={{ fontSize: '1.05rem' }}>MCP allowlist (design)</h2>
        <p style={{ fontSize: 14, color: '#444', lineHeight: 1.5 }}>
          Tool calls will be <strong>deny-by-default</strong> with explicit per-server tool allowlists;
          global and per-project layers should intersect. <code>SENTINEL_MCP_DISABLED_SERVERS</code>{' '}
          currently affects <strong>API introspection only</strong> until the MCP client enforces the same
          rules. See <strong>docs/architecture.md</strong> → Orchestration / MCP plane.
        </p>
      </section>
    </main>
  );
}
