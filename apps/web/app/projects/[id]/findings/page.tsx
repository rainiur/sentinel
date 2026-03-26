import Link from 'next/link';

import { getApiBaseUrl } from '../../../../lib/api-base';

type FindingRow = {
  id: string;
  source: string;
  bug_class: string;
  severity: string | null;
  status: string;
};

export default async function FindingsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const base = getApiBaseUrl();
  let rows: FindingRow[] = [];
  let loadErr: string | null = null;

  try {
    const res = await fetch(`${base}/api/projects/${id}/findings`, { cache: 'no-store' });
    if (res.ok) {
      const data = (await res.json()) as { findings: FindingRow[] };
      rows = data.findings ?? [];
    } else {
      loadErr = res.status === 404 ? 'not_found' : `${res.status}`;
    }
  } catch {
    loadErr = 'unreachable';
  }

  if (loadErr === 'not_found') {
    return (
      <main style={{ fontFamily: 'system-ui, sans-serif', padding: 32 }}>
        <p>Project not found.</p>
        <Link href="/projects">← Projects</Link>
      </main>
    );
  }

  return (
    <main style={{ fontFamily: 'system-ui, sans-serif', padding: 32, maxWidth: 800 }}>
      <p>
        <Link href={`/projects/${id}`}>← Project</Link>
      </p>
      <h1>Findings</h1>
      {loadErr ? <p style={{ color: '#a30' }}>Could not load ({loadErr})</p> : null}
      {rows.length === 0 ? (
        <p style={{ color: '#666' }}>
          No findings yet. Sync via <code>POST /api/sync/findings</code> or{' '}
          <code>pushFindingsToSentinel</code> in the Caido bridge.
        </p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {rows.map((f) => (
            <li
              key={f.id}
              style={{
                marginBottom: 12,
                padding: 12,
                border: '1px solid #ddd',
                borderRadius: 8,
              }}
            >
              <div style={{ fontWeight: 600 }}>{f.bug_class}</div>
              <div style={{ fontSize: 13, color: '#555' }}>
                {f.source}
                {f.severity ? ` · ${f.severity}` : ''} ·{' '}
                <span style={{ textTransform: 'uppercase' }}>{f.status}</span>
              </div>
              <div style={{ fontSize: 11, color: '#888', marginTop: 4 }}>{f.id}</div>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
