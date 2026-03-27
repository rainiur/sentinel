import Link from 'next/link';

import { getApiBaseUrl } from '../../../../lib/api-base';

import { GenerateHypotheses } from './GenerateHypotheses';
import { HypothesesQueue, type HypothesisRow } from './HypothesesQueue';

export default async function HypothesesPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const base = getApiBaseUrl();
  let rows: HypothesisRow[] = [];
  let loadErr: string | null = null;
  let notFound = false;

  try {
    const res = await fetch(`${base}/api/projects/${id}/hypotheses`, { cache: 'no-store' });
    if (res.status === 404) {
      notFound = true;
    } else if (res.ok) {
      const data = (await res.json()) as { hypotheses: HypothesisRow[] };
      rows = data.hypotheses ?? [];
    } else {
      loadErr = `${res.status}`;
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
    <main style={{ fontFamily: 'system-ui, sans-serif', padding: 32, maxWidth: 800 }}>
      <p>
        <Link href={`/projects/${id}`}>← Project</Link>
      </p>
      <h1>Hypotheses</h1>
      {loadErr ? <p style={{ color: '#a30' }}>Could not load ({loadErr})</p> : null}
      <div style={{ marginBottom: 20 }}>
        <GenerateHypotheses projectId={id} />
      </div>
      {rows.length === 0 ? (
        <p style={{ color: '#666' }}>No hypotheses yet. Generate stub rows above.</p>
      ) : (
        <HypothesesQueue hypotheses={rows} />
      )}
    </main>
  );
}
