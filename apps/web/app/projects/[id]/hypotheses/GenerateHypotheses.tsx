'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { getApiBaseUrl } from '../../../../lib/api-base';

export function GenerateHypotheses({ projectId }: { projectId: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function generate() {
    setBusy(true);
    try {
      const base = getApiBaseUrl();
      const res = await fetch(`${base}/api/hypotheses/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_id: projectId, max_results: 3 }),
      });
      if (res.ok) {
        router.refresh();
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      type="button"
      disabled={busy}
      onClick={() => void generate()}
      style={{ padding: '8px 14px', cursor: busy ? 'wait' : 'pointer' }}
    >
      {busy ? 'Generating…' : 'Generate hypotheses (stub)'}
    </button>
  );
}
