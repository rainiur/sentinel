import Link from 'next/link';

import { getApiBaseUrl } from '../../../lib/api-base';

type EndpointRow = {
  id: string;
  method: string;
  route_pattern: string;
  content_type: string | null;
  auth_required: boolean | null;
};

type SurfacePayload = {
  project_id: string;
  endpoints: EndpointRow[];
};

export default async function ProjectDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const base = getApiBaseUrl();
  let name = id;
  let surface: SurfacePayload | null = null;
  let projErr: string | null = null;

  try {
    const [gp, gs] = await Promise.all([
      fetch(`${base}/api/projects/${id}`, { cache: 'no-store' }),
      fetch(`${base}/api/projects/${id}/surface`, { cache: 'no-store' }),
    ]);
    if (gp.ok) {
      const p = (await gp.json()) as { name: string };
      name = p.name;
    } else {
      projErr = gp.status === 404 ? 'not_found' : `project ${gp.status}`;
    }
    if (gs.ok) {
      surface = (await gs.json()) as SurfacePayload;
    }
  } catch {
    projErr = 'unreachable';
  }

  if (projErr === 'not_found') {
    return (
      <main style={{ fontFamily: 'system-ui, sans-serif', padding: 32 }}>
        <p>Project not found.</p>
        <Link href="/projects">← Projects</Link>
      </main>
    );
  }

  return (
    <main style={{ fontFamily: 'system-ui, sans-serif', padding: 32, maxWidth: 900 }}>
      <p>
        <Link href="/projects">← Projects</Link>
      </p>
      <h1>{name}</h1>
      {projErr ? (
        <p style={{ color: '#a30' }}>API issue: {projErr}</p>
      ) : null}
      <p style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <Link href={`/projects/${id}/hypotheses`}>Hypotheses queue →</Link>
        <Link href={`/projects/${id}/findings`}>Findings →</Link>
      </p>
      <h2 style={{ marginTop: 28, fontSize: '1.1rem' }}>Surface (endpoints)</h2>
      {!surface || surface.endpoints.length === 0 ? (
        <p style={{ color: '#666' }}>
          No endpoints yet. Sync traffic via <code>POST /api/sync/requests</code> or the Caido bridge.
        </p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
          <thead>
            <tr style={{ textAlign: 'left', borderBottom: '1px solid #ccc' }}>
              <th style={{ padding: 8 }}>Method</th>
              <th style={{ padding: 8 }}>Path</th>
            </tr>
          </thead>
          <tbody>
            {surface.endpoints.map((e) => (
              <tr key={e.id} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: 8, fontFamily: 'monospace' }}>{e.method}</td>
                <td style={{ padding: 8, fontFamily: 'monospace' }}>{e.route_pattern}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
