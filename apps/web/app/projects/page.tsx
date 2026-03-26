import Link from 'next/link';

import { getApiBaseUrl } from '../../lib/api-base';

import { CreateProjectForm } from './CreateProjectForm';

type ProjectRow = { id: string; name: string; owner_team: string | null };

export default async function ProjectsPage() {
  const base = getApiBaseUrl();
  let projects: ProjectRow[] = [];
  let error: string | null = null;
  try {
    const res = await fetch(`${base}/api/projects`, { cache: 'no-store' });
    if (!res.ok) {
      error = `API ${res.status}`;
    } else {
      const data = (await res.json()) as { projects: ProjectRow[] };
      projects = data.projects ?? [];
    }
  } catch {
    error = 'unreachable';
  }

  return (
    <main style={{ fontFamily: 'system-ui, sans-serif', padding: 32, maxWidth: 720 }}>
      <h1>Projects</h1>
      <CreateProjectForm />
      {error ? (
        <p style={{ color: '#a30' }}>
          Could not load projects ({error}). Is the API running at <code>{base}</code>?
        </p>
      ) : projects.length === 0 ? (
        <p style={{ color: '#666' }}>No projects yet. Use the form above.</p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {projects.map((p) => (
            <li
              key={p.id}
              style={{
                marginBottom: 12,
                padding: 12,
                border: '1px solid #ddd',
                borderRadius: 8,
              }}
            >
              <Link href={`/projects/${p.id}`} style={{ fontWeight: 600 }}>
                {p.name}
              </Link>
              {p.owner_team ? (
                <span style={{ color: '#666', marginLeft: 8 }}>({p.owner_team})</span>
              ) : null}
              <div style={{ fontSize: 12, color: '#888', marginTop: 4 }}>{p.id}</div>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
