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

  return (
    <button
      type="button"
      onClick={() => void approve()}
      style={{ fontSize: 12, padding: '4px 10px', cursor: 'pointer' }}
    >
      Approve
    </button>
  );
}
