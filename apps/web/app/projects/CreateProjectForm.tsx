'use client';

import { useRouter } from 'next/navigation';
import { useState, type FormEvent } from 'react';

import { getApiBaseUrl } from '../../lib/api-base';

export function CreateProjectForm() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [ownerTeam, setOwnerTeam] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    const trimmed = name.trim();
    if (!trimmed) {
      setErr('Name is required');
      return;
    }
    setBusy(true);
    try {
      const base = getApiBaseUrl();
      const res = await fetch(`${base}/api/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: trimmed,
          owner_team: ownerTeam.trim() || null,
        }),
      });
      if (!res.ok) {
        const t = await res.text();
        setErr(`${res.status}: ${t || res.statusText}`);
        return;
      }
      const data = (await res.json()) as { id: string };
      router.push(`/projects/${data.id}`);
      router.refresh();
    } finally {
      setBusy(false);
    }
  }

  return (
    <form
      onSubmit={(e) => void onSubmit(e)}
      style={{
        marginBottom: 28,
        padding: 16,
        border: '1px solid #ddd',
        borderRadius: 8,
        maxWidth: 420,
      }}
    >
      <h2 style={{ margin: '0 0 12px', fontSize: '1rem' }}>New project</h2>
      <label style={{ display: 'block', marginBottom: 8, fontSize: 14 }}>
        Name{' '}
        <input
          name="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          disabled={busy}
          style={{ display: 'block', width: '100%', marginTop: 4, padding: 8 }}
        />
      </label>
      <label style={{ display: 'block', marginBottom: 12, fontSize: 14 }}>
        Owner team (optional){' '}
        <input
          name="owner_team"
          value={ownerTeam}
          onChange={(e) => setOwnerTeam(e.target.value)}
          disabled={busy}
          style={{ display: 'block', width: '100%', marginTop: 4, padding: 8 }}
        />
      </label>
      {err ? <p style={{ color: '#a30', fontSize: 13, marginBottom: 8 }}>{err}</p> : null}
      <button type="submit" disabled={busy} style={{ padding: '8px 16px', cursor: busy ? 'wait' : 'pointer' }}>
        {busy ? 'Creating…' : 'Create'}
      </button>
    </form>
  );
}
