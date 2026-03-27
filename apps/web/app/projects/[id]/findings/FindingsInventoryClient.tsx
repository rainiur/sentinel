'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';

export type FindingRow = {
  id: string;
  source: string;
  bug_class: string;
  severity: string | null;
  confidence: number | null;
  status: string;
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

type SortMode = 'newest' | 'bug_class' | 'severity' | 'confidence';

export function FindingsInventoryClient({
  projectId,
  projectLabel,
  findings,
}: {
  projectId: string;
  projectLabel: string;
  findings: FindingRow[];
}) {
  const [textQ, setTextQ] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sortMode, setSortMode] = useState<SortMode>('newest');
  const [selected, setSelected] = useState<FindingRow | null>(null);

  const severities = useMemo(() => {
    const u = new Set<string>();
    for (const f of findings) {
      if (f.severity) {
        u.add(f.severity);
      }
    }
    return Array.from(u).sort();
  }, [findings]);

  const statuses = useMemo(() => {
    const u = new Set<string>();
    for (const f of findings) {
      u.add(f.status);
    }
    return Array.from(u).sort();
  }, [findings]);

  const rows = useMemo(() => {
    const q = textQ.trim().toLowerCase();
    let out = findings.filter((f) => {
      if (severityFilter) {
        if (severityFilter === '__unset__') {
          if (f.severity) {
            return false;
          }
        } else if ((f.severity || '') !== severityFilter) {
          return false;
        }
      }
      if (statusFilter && f.status !== statusFilter) {
        return false;
      }
      if (q) {
        const hay = `${f.bug_class} ${f.source} ${f.id}`.toLowerCase();
        if (!hay.includes(q)) {
          return false;
        }
      }
      return true;
    });
    out = [...out];
    if (sortMode === 'bug_class') {
      out.sort((a, b) => {
        const c = a.bug_class.localeCompare(b.bug_class);
        return c !== 0 ? c : (a.created_at || '').localeCompare(b.created_at || '');
      });
    } else if (sortMode === 'severity') {
      out.sort((a, b) => (a.severity || '').localeCompare(b.severity || ''));
    } else if (sortMode === 'confidence') {
      out.sort((a, b) => (b.confidence ?? -1) - (a.confidence ?? -1));
    } else {
      out.sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''));
    }
    return out;
  }, [findings, textQ, severityFilter, statusFilter, sortMode]);

  function exportCsv() {
    const header = ['id', 'source', 'bug_class', 'severity', 'confidence', 'status', 'created_at'];
    const lines = [
      header.join(','),
      ...rows.map((f) =>
        [
          csvEscape(f.id),
          csvEscape(f.source),
          csvEscape(f.bug_class),
          csvEscape(f.severity ?? ''),
          f.confidence != null ? String(f.confidence) : '',
          csvEscape(f.status),
          csvEscape(f.created_at ?? ''),
        ].join(','),
      ),
    ];
    downloadBlob(
      `findings-${projectId.slice(0, 8)}.csv`,
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
      findings: rows,
    };
    downloadBlob(
      `findings-${projectId.slice(0, 8)}.json`,
      `${JSON.stringify(payload, null, 2)}\n`,
      'application/json',
    );
  }

  const close = useCallback(() => setSelected(null), []);

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
            Search (class, source, id)
            <input
              value={textQ}
              onChange={(e) => setTextQ(e.target.value)}
              placeholder="xss, caido, …"
              style={{ padding: 8, minWidth: 200 }}
            />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', fontSize: 13, gap: 4 }}>
            Severity
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              style={{ padding: 8, minWidth: 140 }}
            >
              <option value="">All</option>
              <option value="__unset__">(unset)</option>
              {severities.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', fontSize: 13, gap: 4 }}>
            Status
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{ padding: 8, minWidth: 120 }}
            >
              <option value="">All</option>
              {statuses.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', fontSize: 13, gap: 4 }}>
            Sort
            <select
              value={sortMode}
              onChange={(e) => setSortMode(e.target.value as SortMode)}
              style={{ padding: 8, minWidth: 160 }}
            >
              <option value="newest">Newest first</option>
              <option value="bug_class">Bug class A–Z</option>
              <option value="severity">Severity A–Z</option>
              <option value="confidence">Confidence (high first)</option>
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
          Showing <strong>{rows.length}</strong> of {findings.length} findings.
        </p>
      </section>

      {rows.length === 0 ? (
        <p style={{ color: '#666' }}>No findings match the current filters.</p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {rows.map((f) => (
            <li
              key={f.id}
              style={{
                marginBottom: 12,
                padding: 12,
                border: '1px solid #ddd',
                borderRadius: 8,
              }}
            >
              <button
                type="button"
                onClick={() => setSelected(f)}
                style={{
                  width: '100%',
                  textAlign: 'left',
                  background: 'none',
                  border: 'none',
                  padding: 0,
                  cursor: 'pointer',
                  font: 'inherit',
                }}
              >
                <div style={{ fontWeight: 600 }}>{f.bug_class}</div>
                <div style={{ fontSize: 13, color: '#555' }}>
                  {f.source}
                  {f.severity ? ` · ${f.severity}` : ''}
                  {f.confidence != null ? ` · conf ${Number(f.confidence).toFixed(2)}` : ''} ·{' '}
                  <span style={{ textTransform: 'uppercase' }}>{f.status}</span>
                </div>
                <div style={{ fontSize: 11, color: '#888', marginTop: 4 }}>{f.id}</div>
                <div style={{ fontSize: 12, color: '#06c', marginTop: 6 }}>View details →</div>
              </button>
            </li>
          ))}
        </ul>
      )}

      {selected ? (
        <>
          <button
            type="button"
            aria-label="Close finding details"
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
            aria-labelledby="finding-drawer-title"
            style={{
              position: 'fixed',
              top: 0,
              right: 0,
              bottom: 0,
              width: 'min(100vw, 420px)',
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
              <h2 id="finding-drawer-title" style={{ margin: '0 0 8px', fontSize: '1.1rem' }}>
                Finding detail
              </h2>
              <button type="button" onClick={close} style={{ padding: '4px 10px', cursor: 'pointer' }}>
                Close
              </button>
            </div>
            <p style={{ margin: '0 0 16px', fontSize: 13, color: '#555', wordBreak: 'break-all' }}>
              {selected.id}
            </p>
            <dl style={{ margin: 0, fontSize: 14 }}>
              <dt style={{ fontWeight: 600, marginTop: 12 }}>Bug class</dt>
              <dd style={{ margin: '4px 0 0' }}>{selected.bug_class}</dd>
              <dt style={{ fontWeight: 600, marginTop: 12 }}>Source</dt>
              <dd style={{ margin: '4px 0 0' }}>{selected.source}</dd>
              <dt style={{ fontWeight: 600, marginTop: 12 }}>Severity</dt>
              <dd style={{ margin: '4px 0 0' }}>{selected.severity ?? '—'}</dd>
              <dt style={{ fontWeight: 600, marginTop: 12 }}>Confidence</dt>
              <dd style={{ margin: '4px 0 0' }}>
                {selected.confidence != null ? Number(selected.confidence).toFixed(4) : '—'}
              </dd>
              <dt style={{ fontWeight: 600, marginTop: 12 }}>Status</dt>
              <dd style={{ margin: '4px 0 0', textTransform: 'uppercase' }}>{selected.status}</dd>
              <dt style={{ fontWeight: 600, marginTop: 12 }}>Created</dt>
              <dd style={{ margin: '4px 0 0', fontSize: 13 }}>{selected.created_at ?? '—'}</dd>
            </dl>
          </aside>
        </>
      ) : null}
    </>
  );
}
