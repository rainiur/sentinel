import Link from 'next/link';

import { getApiBaseUrl } from '../../../../lib/api-base';

import { SurfaceInventoryClient, type EndpointRow } from './SurfaceInventoryClient';

type SurfacePayload = {
  project_id: string;
  endpoints: EndpointRow[];
};

function NotFound() {
  return (
    <main style={{ fontFamily: 'system-ui, sans-serif', padding: 32 }}>
      <p>Project not found.</p>
      <Link href="/projects">← Projects</Link>
    </main>
  );
}

export default async function SurfaceInventoryPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const base = getApiBaseUrl();
  let name = id;
  let endpoints: EndpointRow[] = [];
  let loadErr: string | null = null;
  let notFound = false;

  try {
    const [gp, gs] = await Promise.all([
      fetch(`${base}/api/projects/${id}`, { cache: 'no-store' }),
      fetch(`${base}/api/projects/${id}/surface`, { cache: 'no-store' }),
    ]);
    if (gp.status === 404 || gs.status === 404) {
      notFound = true;
    } else {
      if (gp.ok) {
        const p = (await gp.json()) as { name: string };
        name = p.name;
      } else {
        loadErr = `project ${gp.status}`;
      }
      if (gs.ok) {
        const s = (await gs.json()) as SurfacePayload;
        endpoints = s.endpoints ?? [];
      } else {
        loadErr = loadErr ?? `surface ${gs.status}`;
      }
    }
  } catch {
    loadErr = 'unreachable';
  }

  if (notFound) {
    return <NotFound />;
  }

  return (
    <main style={{ fontFamily: 'system-ui, sans-serif', padding: 32, maxWidth: 1000 }}>
      <p>
        <Link href={`/projects/${id}`}>← Project</Link>
      </p>
      <h1>Surface inventory</h1>
      <p style={{ color: '#555', marginTop: 0 }}>
        <strong>{name}</strong> — endpoints observed from synced traffic (query strings grouped).
      </p>
      {loadErr ? <p style={{ color: '#a30' }}>Could not load fully ({loadErr})</p> : null}
      <SurfaceInventoryClient projectId={id} projectName={name} endpoints={endpoints} />
    </main>
  );
}
