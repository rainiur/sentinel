import Link from 'next/link';

import { getApiBaseUrl } from '../../lib/api-base';

type VersionPayload = {
  version: string;
  service: string;
  writes_disabled?: boolean;
};

type McpPayload = {
  loaded: boolean;
  path_configured: boolean;
  error: string | null;
  server_count: number;
  servers: { name: string; transport: string }[];
};

export default async function DashboardPage() {
  const base = getApiBaseUrl();
  let health = 'unknown';
  let version: VersionPayload | null = null;
  let projectCount: number | null = null;
  let mcp: McpPayload | null = null;
  let err: string | null = null;

  try {
    const [h, v, p, m] = await Promise.all([
      fetch(`${base}/health`, { cache: 'no-store' }),
      fetch(`${base}/api/version`, { cache: 'no-store' }),
      fetch(`${base}/api/projects`, { cache: 'no-store' }),
      fetch(`${base}/api/mcp/servers`, { cache: 'no-store' }),
    ]);
    if (h.ok) {
      const hj = (await h.json()) as { status?: string };
      health = hj.status ?? 'ok';
    }
    if (v.ok) {
      version = (await v.json()) as VersionPayload;
    }
    if (p.ok) {
      const pj = (await p.json()) as { projects?: unknown[] };
      projectCount = pj.projects?.length ?? 0;
    }
    if (m.ok) {
      mcp = (await m.json()) as McpPayload;
    }
    if (!v.ok || !p.ok || !m.ok) {
      err = 'Some API calls failed (check auth and base URL).';
    }
  } catch {
    err = 'API unreachable';
  }

  return (
    <main style={{ fontFamily: 'system-ui, sans-serif', padding: 32, maxWidth: 720 }}>
      <h1>Dashboard</h1>
      {err ? <p style={{ color: '#a30' }}>{err}</p> : null}
      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: '1.05rem' }}>Status</h2>
        <ul>
          <li>
            Health: <strong>{health}</strong>
          </li>
          {version ? (
            <>
              <li>
                API version: <strong>{version.version}</strong> ({version.service})
              </li>
              <li>
                Writes disabled:{' '}
                <strong>{version.writes_disabled ? 'yes (maintenance)' : 'no'}</strong>
              </li>
            </>
          ) : null}
          {projectCount !== null ? (
            <li>
              Projects: <strong>{projectCount}</strong>
            </li>
          ) : null}
        </ul>
      </section>
      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: '1.05rem' }}>MCP config</h2>
        {!mcp ? (
          <p style={{ color: '#666' }}>Could not load MCP summary.</p>
        ) : (
          <ul>
            <li>
              Config path set: <strong>{mcp.path_configured ? 'yes' : 'no'}</strong>
            </li>
            <li>
              Loaded: <strong>{mcp.loaded ? 'yes' : 'no'}</strong>
              {mcp.error ? (
                <span style={{ color: '#a30' }}> ({mcp.error})</span>
              ) : null}
            </li>
            <li>
              Servers: <strong>{mcp.server_count}</strong>
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
        <p style={{ fontSize: 13, color: '#555' }}>
          Configure <code>SENTINEL_MCP_CONFIG</code> on the API (see <code>config/mcp.example.json</code>).
        </p>
      </section>
      <p>
        <Link href="/projects">Manage projects →</Link>
      </p>
    </main>
  );
}
