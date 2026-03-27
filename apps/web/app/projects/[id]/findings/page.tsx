import Link from 'next/link';

import { getApiBaseUrl } from '../../../../lib/api-base';

import { FindingsInventoryClient, type FindingRow } from './FindingsInventoryClient';

export default async function FindingsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const base = getApiBaseUrl();
  let name = id;
  let rows: FindingRow[] = [];
  let loadErr: string | null = null;
  let notFound = false;

  try {
    const [gp, gf] = await Promise.all([
      fetch(`${base}/api/projects/${id}`, { cache: 'no-store' }),
      fetch(`${base}/api/projects/${id}/findings`, { cache: 'no-store' }),
    ]);
    if (gp.status === 404 || gf.status === 404) {
      notFound = true;
    } else {
      if (gp.ok) {
        const p = (await gp.json()) as { name: string };
        name = p.name;
      } else {
        loadErr = `project ${gp.status}`;
      }
      if (gf.ok) {
        const data = (await gf.json()) as { findings: FindingRow[] };
        rows = data.findings ?? [];
      } else {
        loadErr = loadErr ?? `findings ${gf.status}`;
      }
    }
  } catch {
    loadErr = 'unreachable';
  }

  if (notFound) {
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
        <Link href={`/projects/${id}`}>← Project</Link>
      </p>
      <h1>Findings</h1>
      <p style={{ color: '#555', marginTop: 0 }}>
        <strong>{name}</strong> — synced from Caido or <code>POST /api/sync/findings</code>.
      </p>
      {loadErr ? <p style={{ color: '#a30' }}>Could not load fully ({loadErr})</p> : null}
      {rows.length === 0 ? (
        <p style={{ color: '#666' }}>
          No findings yet. Sync via <code>POST /api/sync/findings</code> or{' '}
          <code>pushFindingsToSentinel</code> in the Caido bridge.
        </p>
      ) : (
        <FindingsInventoryClient projectId={id} projectLabel={name} findings={rows} />
      )}
    </main>
  );
}
