'use client';

import { useRouter } from 'next/navigation';

import { getApiBaseUrl } from '../../../../lib/api-base';

export function HypothesisActions({ hypothesisId }: { hypothesisId: string }) {
  const router = useRouter();

  async function approve() {
    const base = getApiBaseUrl();
    const res = await fetch(`${base}/api/hypotheses/${hypothesisId}/approve`, {
      method: 'POST',
    });
    if (res.ok) {
      router.refresh();
    }
  }

  async function reject() {
    const base = getApiBaseUrl();
    const res = await fetch(`${base}/api/hypotheses/${hypothesisId}/reject`, {
      method: 'POST',
    });
    if (res.ok) {
      router.refresh();
    }
  }

  return (
    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
      <button
        type="button"
        onClick={() => void approve()}
        style={{ fontSize: 12, padding: '4px 10px', cursor: 'pointer' }}
      >
        Approve
      </button>
      <button
        type="button"
        onClick={() => void reject()}
        style={{ fontSize: 12, padding: '4px 10px', cursor: 'pointer' }}
      >
        Reject
      </button>
    </div>
  );
}
