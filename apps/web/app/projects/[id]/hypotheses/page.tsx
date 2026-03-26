import Link from 'next/link';

import { getApiBaseUrl } from '../../../../lib/api-base';

import { GenerateHypotheses } from './GenerateHypotheses';
import { HypothesisActions } from './HypothesisActions';

type HypothesisRow = {
  id: string;
  title: string;
  bug_class: string;
  status: string;
  priority_score?: number | null;
};

export default async function HypothesesPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const base = getApiBaseUrl();
  let rows: HypothesisRow[] = [];
  let loadErr: string | null = null;

  try {
    const res = await fetch(`${base}/api/projects/${id}/hypotheses`, { cache: 'no-store' });
    if (res.ok) {
      const data = (await res.json()) as { hypotheses: HypothesisRow[] };
      rows = data.hypotheses ?? [];
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
      <h1>Hypotheses</h1>
      {loadErr ? <p style={{ color: '#a30' }}>Could not load ({loadErr})</p> : null}
      <div style={{ marginBottom: 20 }}>
        <GenerateHypotheses projectId={id} />
      </div>
      {rows.length === 0 ? (
        <p style={{ color: '#666' }}>No hypotheses yet. Generate stub rows above.</p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {rows.map((h) => (
            <li
              key={h.id}
              style={{
                marginBottom: 12,
                padding: 12,
                border: '1px solid #ddd',
                borderRadius: 8,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                gap: 12,
              }}
            >
              <div>
                <div style={{ fontWeight: 600 }}>{h.title}</div>
                <div style={{ fontSize: 13, color: '#555' }}>
                  {h.bug_class} · <span style={{ textTransform: 'uppercase' }}>{h.status}</span>
                </div>
                <div style={{ fontSize: 11, color: '#888', marginTop: 4 }}>{h.id}</div>
              </div>
              {h.status === 'queued' ? (
                <HypothesisActions hypothesisId={h.id} />
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
