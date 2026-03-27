'use client';

import { useMemo, useState } from 'react';

export type BundleRow = {
  id: string;
  storage_key: string;
  summary: string | null;
  created_at?: string | null;
};

function csvEscape(s: string) {
  if (/[",\n\r]/.test(s)) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

function downloadBlob(filename: string, body: string, mime: string) {
  const blob = new Blob([body], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

type SortMode = 'newest' | 'storage_key' | 'summary';

export function EvidenceBundlesClient({
  projectId,
  projectLabel,
  bundles,
}: {
  projectId: string;
  projectLabel: string;
  bundles: BundleRow[];
}) {
  const [keyQ, setKeyQ] = useState('');
  const [summaryQ, setSummaryQ] = useState('');
  const [sortMode, setSortMode] = useState<SortMode>('newest');

  const rows = useMemo(() => {
    const kq = keyQ.trim().toLowerCase();
    const sq = summaryQ.trim().toLowerCase();
    let out = bundles.filter((b) => {
      if (kq && !b.storage_key.toLowerCase().includes(kq)) {
        return false;
      }
      if (sq && !(b.summary || '').toLowerCase().includes(sq)) {
        return false;
      }
      return true;
    });
    out = [...out];
    if (sortMode === 'storage_key') {
      out.sort((a, b) => a.storage_key.localeCompare(b.storage_key));
    } else if (sortMode === 'summary') {
      out.sort((a, b) => (a.summary || '').localeCompare(b.summary || ''));
    } else {
      out.sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''));
    }
    return out;
  }, [bundles, keyQ, summaryQ, sortMode]);

  function exportCsv() {
    const header = ['id', 'storage_key', 'summary', 'created_at'];
    const lines = [
      header.join(','),
      ...rows.map((b) =>
        [
          csvEscape(b.id),
          csvEscape(b.storage_key),
          csvEscape(b.summary ?? ''),
          csvEscape(b.created_at ?? ''),
        ].join(','),
      ),
    ];
    downloadBlob(
      `evidence-${projectId.slice(0, 8)}.csv`,
      lines.join('\n'),
      'text/csv;charset=utf-8',
    );
  }

  function exportJson() {
    const payload = {
      project_id: projectId,
      project_label: projectLabel,
      exported_at: new Date().toISOString(),
      count: rows.length,
      bundles: rows,
    };
    downloadBlob(
      `evidence-${projectId.slice(0, 8)}.json`,
      `${JSON.stringify(payload, null, 2)}\n`,
      'application/json',
    );
  }

  return (
    <>
      <section
        style={{
          marginBottom: 20,
          padding: 16,
          border: '1px solid #ddd',
          borderRadius: 8,
          maxWidth: 960,
        }}
      >
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'flex-end' }}>
          <label style={{ display: 'flex', flexDirection: 'column', fontSize: 13, gap: 4 }}>
            Storage key contains
            <input
              value={keyQ}
              onChange={(e) => setKeyQ(e.target.value)}
              placeholder="evidence/…"
              style={{ padding: 8, minWidth: 220 }}
            />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', fontSize: 13, gap: 4 }}>
            Summary contains
            <input
              value={summaryQ}
              onChange={(e) => setSummaryQ(e.target.value)}
              style={{ padding: 8, minWidth: 180 }}
            />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', fontSize: 13, gap: 4 }}>
            Sort
            <select
              value={sortMode}
              onChange={(e) => setSortMode(e.target.value as SortMode)}
              style={{ padding: 8, minWidth: 160 }}
            >
              <option value="newest">Newest first</option>
              <option value="storage_key">Storage key A–Z</option>
              <option value="summary">Summary A–Z</option>
            </select>
          </label>
          <button type="button" onClick={exportCsv} style={{ padding: '8px 14px', cursor: 'pointer' }}>
            Export CSV
          </button>
          <button type="button" onClick={exportJson} style={{ padding: '8px 14px', cursor: 'pointer' }}>
            Export JSON
          </button>
        </div>
        <p style={{ margin: '12px 0 0', fontSize: 13, color: '#555' }}>
          Showing <strong>{rows.length}</strong> of {bundles.length} bundles.
        </p>
      </section>

      {rows.length === 0 ? (
        <p style={{ color: '#666' }}>No bundles match the current filters.</p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {rows.map((b) => (
            <li
              key={b.id}
              style={{
                marginBottom: 12,
                padding: 12,
                border: '1px solid #ddd',
                borderRadius: 8,
              }}
            >
              <div style={{ fontFamily: 'monospace', fontSize: 13, wordBreak: 'break-all' }}>
                {b.storage_key}
              </div>
              {b.summary ? (
                <div style={{ fontSize: 13, color: '#555', marginTop: 6 }}>{b.summary}</div>
              ) : null}
              <div style={{ fontSize: 11, color: '#888', marginTop: 4 }}>
                {b.id}
                {b.created_at ? ` · ${b.created_at}` : ''}
              </div>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
