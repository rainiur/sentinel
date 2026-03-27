import Link from 'next/link';

import { getApiBaseUrl } from '../../../../lib/api-base';

import { EvidenceBundlesClient, type BundleRow } from './EvidenceBundlesClient';
import { RegisterEvidenceForm } from './RegisterEvidenceForm';

export default async function EvidencePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const base = getApiBaseUrl();
  let name = id;
  let bundles: BundleRow[] = [];
  let loadErr: string | null = null;
  let notFound = false;

  try {
    const [gp, ge] = await Promise.all([
      fetch(`${base}/api/projects/${id}`, { cache: 'no-store' }),
      fetch(`${base}/api/projects/${id}/evidence`, { cache: 'no-store' }),
    ]);
    if (gp.status === 404 || ge.status === 404) {
      notFound = true;
    } else {
      if (gp.ok) {
        const p = (await gp.json()) as { name: string };
        name = p.name;
      } else {
        loadErr = `project ${gp.status}`;
      }
      if (ge.ok) {
        const data = (await ge.json()) as { bundles: BundleRow[] };
        bundles = data.bundles ?? [];
      } else {
        loadErr = loadErr ?? `evidence ${ge.status}`;
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
      <h1>Evidence bundles</h1>
      <p style={{ color: '#555', marginTop: 0 }}>
        <strong>{name}</strong> — metadata for objects in S3-compatible storage.
      </p>
      {loadErr ? <p style={{ color: '#a30' }}>Could not load fully ({loadErr})</p> : null}
      <RegisterEvidenceForm projectId={id} />
      {bundles.length === 0 ? (
        <p style={{ color: '#666' }}>No bundles registered yet.</p>
      ) : (
        <EvidenceBundlesClient projectId={id} projectLabel={name} bundles={bundles} />
      )}
    </main>
  );
}
