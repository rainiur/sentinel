import Link from 'next/link';

import { getApiBaseUrl } from '../../../../lib/api-base';

import { RegisterEvidenceForm } from './RegisterEvidenceForm';

type BundleRow = {
  id: string;
  storage_key: string;
  summary: string | null;
};

export default async function EvidencePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const base = getApiBaseUrl();
  let bundles: BundleRow[] = [];
  let loadErr: string | null = null;

  try {
    const res = await fetch(`${base}/api/projects/${id}/evidence`, { cache: 'no-store' });
    if (res.ok) {
      const data = (await res.json()) as { bundles: BundleRow[] };
      bundles = data.bundles ?? [];
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
      <h1>Evidence bundles</h1>
      {loadErr ? <p style={{ color: '#a30' }}>Could not load ({loadErr})</p> : null}
      <RegisterEvidenceForm projectId={id} />
      {bundles.length === 0 ? (
        <p style={{ color: '#666' }}>No bundles registered yet.</p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {bundles.map((b) => (
            <li
              key={b.id}
              style={{
                marginBottom: 12,
                padding: 12,
                border: '1px solid #ddd',
                borderRadius: 8,
              }}
            >
              <div style={{ fontFamily: 'monospace', fontSize: 13, wordBreak: 'break-all' }}>
                {b.storage_key}
              </div>
              {b.summary ? (
                <div style={{ fontSize: 13, color: '#555', marginTop: 6 }}>{b.summary}</div>
              ) : null}
              <div style={{ fontSize: 11, color: '#888', marginTop: 4 }}>{b.id}</div>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
