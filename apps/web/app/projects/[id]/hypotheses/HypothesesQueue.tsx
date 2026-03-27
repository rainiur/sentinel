'use client';

import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';

import { getApiBaseUrl } from '../../../../lib/api-base';

export type HypothesisRow = {
  id: string;
  title: string;
  bug_class: string;
  status: string;
  priority_score?: number | null;
  confidence_score?: number | null;
  created_at?: string | null;
  rationale?: string;
  supporting_evidence?: unknown[];
  human_approval_required?: boolean;
  proposed_template_id?: string | null;
};

export function HypothesesQueue({ hypotheses }: { hypotheses: HypothesisRow[] }) {
  const router = useRouter();
  const [selected, setSelected] = useState<HypothesisRow | null>(null);
  const [actionErr, setActionErr] = useState<string | null>(null);

  const close = useCallback(() => {
    setSelected(null);
    setActionErr(null);
  }, []);

  useEffect(() => {
    if (!selected) {
      return undefined;
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        close();
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [selected, close]);

  async function approve(id: string) {
    setActionErr(null);
    const base = getApiBaseUrl();
    const res = await fetch(`${base}/api/hypotheses/${id}/approve`, { method: 'POST' });
    if (!res.ok) {
      const t = await res.text();
      setActionErr(`${res.status}: ${t || res.statusText}`);
      return;
    }
    close();
    router.refresh();
  }

  async function reject(id: string) {
    setActionErr(null);
    const base = getApiBaseUrl();
    const res = await fetch(`${base}/api/hypotheses/${id}/reject`, { method: 'POST' });
    if (!res.ok) {
      const t = await res.text();
      setActionErr(`${res.status}: ${t || res.statusText}`);
      return;
    }
    close();
    router.refresh();
  }

  const evJson =
    selected && selected.supporting_evidence && selected.supporting_evidence.length > 0
      ? JSON.stringify(selected.supporting_evidence, null, 2)
      : null;

  return (
    <>
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {hypotheses.map((h) => (
          <li
            key={h.id}
            style={{
              marginBottom: 12,
              padding: 12,
              border: '1px solid #ddd',
              borderRadius: 8,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              gap: 12,
            }}
          >
            <button
              type="button"
              onClick={() => {
                setSelected(h);
                setActionErr(null);
              }}
              style={{
                flex: 1,
                textAlign: 'left',
                background: 'none',
                border: 'none',
                padding: 0,
                cursor: 'pointer',
                font: 'inherit',
              }}
            >
              <div style={{ fontWeight: 600 }}>{h.title}</div>
              <div style={{ fontSize: 13, color: '#555' }}>
                {h.bug_class} · <span style={{ textTransform: 'uppercase' }}>{h.status}</span>
                {h.priority_score != null ? ` · p=${Number(h.priority_score).toFixed(2)}` : null}
              </div>
              <div style={{ fontSize: 11, color: '#888', marginTop: 4 }}>{h.id}</div>
              <div style={{ fontSize: 12, color: '#06c', marginTop: 6 }}>View details →</div>
            </button>
            {h.status === 'queued' ? (
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', flexShrink: 0 }}>
                <button
                  type="button"
                  onClick={() => void approve(h.id)}
                  style={{ fontSize: 12, padding: '4px 10px', cursor: 'pointer' }}
                >
                  Approve
                </button>
                <button
                  type="button"
                  onClick={() => void reject(h.id)}
                  style={{ fontSize: 12, padding: '4px 10px', cursor: 'pointer' }}
                >
                  Reject
                </button>
              </div>
            ) : null}
          </li>
        ))}
      </ul>

      {selected ? (
        <>
          <button
            type="button"
            aria-label="Close hypothesis details"
            onClick={close}
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 40,
              border: 'none',
              margin: 0,
              padding: 0,
              background: 'rgba(0,0,0,0.25)',
              cursor: 'pointer',
            }}
          />
          <aside
            role="dialog"
            aria-modal="true"
            aria-labelledby="hypothesis-drawer-title"
            style={{
              position: 'fixed',
              top: 0,
              right: 0,
              bottom: 0,
              width: 'min(100vw, 440px)',
              zIndex: 50,
              background: '#fff',
              borderLeft: '1px solid #ccc',
              boxShadow: '-4px 0 24px rgba(0,0,0,0.12)',
              padding: 20,
              overflowY: 'auto',
              fontFamily: 'system-ui, sans-serif',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
              <h2 id="hypothesis-drawer-title" style={{ margin: '0 0 8px', fontSize: '1.1rem' }}>
                Hypothesis detail
              </h2>
              <button type="button" onClick={close} style={{ padding: '4px 10px', cursor: 'pointer' }}>
                Close
              </button>
            </div>
            <p style={{ margin: '0 0 16px', fontSize: 13, color: '#555', wordBreak: 'break-all' }}>
              {selected.id}
            </p>
            <dl style={{ margin: 0, fontSize: 14 }}>
              <dt style={{ fontWeight: 600, marginTop: 12 }}>Title</dt>
              <dd style={{ margin: '4px 0 0' }}>{selected.title}</dd>
              <dt style={{ fontWeight: 600, marginTop: 12 }}>Bug class</dt>
              <dd style={{ margin: '4px 0 0' }}>{selected.bug_class}</dd>
              <dt style={{ fontWeight: 600, marginTop: 12 }}>Status</dt>
              <dd style={{ margin: '4px 0 0', textTransform: 'uppercase' }}>{selected.status}</dd>
              <dt style={{ fontWeight: 600, marginTop: 12 }}>Priority / confidence</dt>
              <dd style={{ margin: '4px 0 0' }}>
                {selected.priority_score != null ? Number(selected.priority_score).toFixed(4) : '—'} /{' '}
                {selected.confidence_score != null ? Number(selected.confidence_score).toFixed(4) : '—'}
              </dd>
              <dt style={{ fontWeight: 600, marginTop: 12 }}>Human approval required</dt>
              <dd style={{ margin: '4px 0 0' }}>{selected.human_approval_required !== false ? 'yes' : 'no'}</dd>
              {selected.proposed_template_id ? (
                <>
                  <dt style={{ fontWeight: 600, marginTop: 12 }}>Proposed template</dt>
                  <dd style={{ margin: '4px 0 0', fontFamily: 'monospace', fontSize: 12 }}>
                    {selected.proposed_template_id}
                  </dd>
                </>
              ) : null}
              {selected.created_at ? (
                <>
                  <dt style={{ fontWeight: 600, marginTop: 12 }}>Created</dt>
                  <dd style={{ margin: '4px 0 0', fontSize: 13 }}>{selected.created_at}</dd>
                </>
              ) : null}
              <dt style={{ fontWeight: 600, marginTop: 12 }}>Rationale</dt>
              <dd style={{ margin: '4px 0 0', whiteSpace: 'pre-wrap' }}>{selected.rationale || '—'}</dd>
              {evJson ? (
                <>
                  <dt style={{ fontWeight: 600, marginTop: 12 }}>Supporting evidence (JSON)</dt>
                  <dd style={{ margin: '4px 0 0' }}>
                    <pre
                      style={{
                        fontSize: 11,
                        background: '#f6f6f6',
                        padding: 10,
                        borderRadius: 6,
                        overflowX: 'auto',
                        maxHeight: 200,
                      }}
                    >
                      {evJson}
                    </pre>
                  </dd>
                </>
              ) : null}
            </dl>
            {selected.status === 'queued' ? (
              <div style={{ marginTop: 24, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button type="button" onClick={() => void approve(selected.id)} style={{ padding: '8px 16px' }}>
                  Approve
                </button>
                <button type="button" onClick={() => void reject(selected.id)} style={{ padding: '8px 16px' }}>
                  Reject
                </button>
              </div>
            ) : null}
            {actionErr ? (
              <p style={{ color: '#a30', fontSize: 13, marginTop: 12 }} role="alert">
                {actionErr}
              </p>
            ) : null}
          </aside>
        </>
      ) : null}
    </>
  );
}
