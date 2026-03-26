'use client';

import { useRouter } from 'next/navigation';
import { useState, type FormEvent } from 'react';

import { getApiBaseUrl } from '../../../../lib/api-base';

export function RegisterEvidenceForm({ projectId }: { projectId: string }) {
  const router = useRouter();
  const [storageKey, setStorageKey] = useState('');
  const [summary, setSummary] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    const sk = storageKey.trim();
    if (!sk) {
      setErr('Storage key is required');
      return;
    }
    setBusy(true);
    try {
      const base = getApiBaseUrl();
      const res = await fetch(`${base}/api/projects/${projectId}/evidence`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          storage_key: sk,
          summary: summary.trim() || null,
        }),
      });
      if (!res.ok) {
        const t = await res.text();
        setErr(`${res.status}: ${t || res.statusText}`);
        return;
      }
      setStorageKey('');
      setSummary('');
      router.refresh();
    } finally {
      setBusy(false);
    }
  }

  return (
    <form
      onSubmit={(e) => void onSubmit(e)}
      style={{
        marginBottom: 24,
        padding: 16,
        border: '1px solid #ddd',
        borderRadius: 8,
        maxWidth: 520,
      }}
    >
      <h2 style={{ margin: '0 0 12px', fontSize: '1rem' }}>Register evidence (metadata)</h2>
      <p style={{ fontSize: 13, color: '#555', marginTop: 0 }}>
        Upload the object to MinIO/S3 first, then record the <strong>storage key</strong> here.
      </p>
      <label style={{ display: 'block', marginBottom: 8, fontSize: 14 }}>
        Storage key
        <input
          value={storageKey}
          onChange={(e) => setStorageKey(e.target.value)}
          required
          disabled={busy}
          placeholder="e.g. evidence/proj-id/file.bin"
          style={{ display: 'block', width: '100%', marginTop: 4, padding: 8 }}
        />
      </label>
      <label style={{ display: 'block', marginBottom: 12, fontSize: 14 }}>
        Summary (optional)
        <input
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
          disabled={busy}
          style={{ display: 'block', width: '100%', marginTop: 4, padding: 8 }}
        />
      </label>
      {err ? <p style={{ color: '#a30', fontSize: 13, marginBottom: 8 }}>{err}</p> : null}
      <button type="submit" disabled={busy} style={{ padding: '8px 16px', cursor: busy ? 'wait' : 'pointer' }}>
        {busy ? 'Saving…' : 'Register'}
      </button>
    </form>
  );
}
