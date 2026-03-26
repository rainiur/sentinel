'use client';

import { useRouter } from 'next/navigation';
import { useRef, useState, type FormEvent } from 'react';

import { getApiBaseUrl } from '../../../../lib/api-base';

type PresignPayload = {
  upload_url: string;
  storage_key: string;
  http_method: string;
  content_type: string;
  expires_in: number;
};

export function RegisterEvidenceForm({ projectId }: { projectId: string }) {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [storageKey, setStorageKey] = useState('');
  const [summary, setSummary] = useState('');
  const [uploadSummary, setUploadSummary] = useState('');
  const [busy, setBusy] = useState(false);
  const [uploadBusy, setUploadBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [uploadErr, setUploadErr] = useState<string | null>(null);

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

  async function onUploadPresigned() {
    setUploadErr(null);
    const input = fileInputRef.current;
    const file = input?.files?.[0];
    if (!file) {
      setUploadErr('Choose a file first');
      return;
    }
    setUploadBusy(true);
    try {
      const base = getApiBaseUrl();
      const pres = await fetch(`${base}/api/projects/${projectId}/evidence/presign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: file.name,
          content_type: file.type || undefined,
        }),
      });
      if (pres.status === 503) {
        setUploadErr(
          'Presign is unavailable (API needs S3_*/MinIO env). Use manual storage key below or configure the API.',
        );
        return;
      }
      if (!pres.ok) {
        const t = await pres.text();
        setUploadErr(`${pres.status}: ${t || pres.statusText}`);
        return;
      }
      const data = (await pres.json()) as PresignPayload;
      const put = await fetch(data.upload_url, {
        method: data.http_method,
        body: file,
        headers: { 'Content-Type': data.content_type },
      });
      if (!put.ok) {
        setUploadErr(
          `Upload to storage failed (${put.status}). If this is a browser upload to MinIO/S3, configure CORS on the bucket.`,
        );
        return;
      }
      const reg = await fetch(`${base}/api/projects/${projectId}/evidence`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          storage_key: data.storage_key,
          summary: uploadSummary.trim() || null,
        }),
      });
      if (!reg.ok) {
        const t = await reg.text();
        setUploadErr(`${reg.status}: ${t || reg.statusText}`);
        return;
      }
      setUploadSummary('');
      if (input) input.value = '';
      router.refresh();
    } finally {
      setUploadBusy(false);
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
      <h2 style={{ margin: '0 0 12px', fontSize: '1rem' }}>Upload via presigned URL</h2>
      <p style={{ fontSize: 13, color: '#555', marginTop: 0 }}>
        Requests a short-lived PUT URL from the API, uploads the file, then registers metadata. Direct
        browser uploads require <strong>CORS</strong> on your MinIO/S3 bucket.
      </p>
      <input
        ref={fileInputRef}
        type="file"
        disabled={uploadBusy}
        style={{ display: 'block', marginBottom: 8, fontSize: 14 }}
      />
      <label style={{ display: 'block', marginBottom: 12, fontSize: 14 }}>
        Summary (optional)
        <input
          value={uploadSummary}
          onChange={(e) => setUploadSummary(e.target.value)}
          disabled={uploadBusy}
          style={{ display: 'block', width: '100%', marginTop: 4, padding: 8 }}
        />
      </label>
      {uploadErr ? <p style={{ color: '#a30', fontSize: 13, marginBottom: 8 }}>{uploadErr}</p> : null}
      <button
        type="button"
        disabled={uploadBusy}
        onClick={() => void onUploadPresigned()}
        style={{ padding: '8px 16px', marginBottom: 24, cursor: uploadBusy ? 'wait' : 'pointer' }}
      >
        {uploadBusy ? 'Uploading…' : 'Upload & register'}
      </button>

      <h2 style={{ margin: '0 0 12px', fontSize: '1rem' }}>Register evidence (metadata only)</h2>
      <p style={{ fontSize: 13, color: '#555', marginTop: 0 }}>
        If you already uploaded the object (e.g. with <code>mc</code> or the MinIO console), record the{' '}
        <strong>storage key</strong> here.
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
