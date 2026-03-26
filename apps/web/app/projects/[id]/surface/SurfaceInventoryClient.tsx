'use client';

import { useMemo, useState } from 'react';

export type EndpointRow = {
  id: string;
  method: string;
  route_pattern: string;
  content_type: string | null;
  auth_required: boolean | null;
};

type SortKey = 'method' | 'path';

function downloadBlob(filename: string, body: string, mime: string) {
  const blob = new Blob([body], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function csvEscape(s: string) {
  if (/[",\n\r]/.test(s)) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

export function SurfaceInventoryClient({
  projectId,
  projectName,
  endpoints,
}: {
  projectId: string;
  projectName: string;
  endpoints: EndpointRow[];
}) {
  const [pathQuery, setPathQuery] = useState('');
  const [methodFilter, setMethodFilter] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('path');

  const methods = useMemo(() => {
    const u = new Set<string>();
    for (const e of endpoints) {
      u.add((e.method || 'GET').toUpperCase());
    }
    return Array.from(u).sort();
  }, [endpoints]);

  const rows = useMemo(() => {
    const q = pathQuery.trim().toLowerCase();
    const out = endpoints.filter((e) => {
      const m = (e.method || 'GET').toUpperCase();
      if (methodFilter && m !== methodFilter) {
        return false;
      }
      if (q && !e.route_pattern.toLowerCase().includes(q)) {
        return false;
      }
      return true;
    });
    return [...out].sort((a, b) => {
      if (sortKey === 'method') {
        const cm = (a.method || '').localeCompare(b.method || '');
        if (cm !== 0) {
          return cm;
        }
        return a.route_pattern.localeCompare(b.route_pattern);
      }
      const cp = a.route_pattern.localeCompare(b.route_pattern);
      if (cp !== 0) {
        return cp;
      }
      return (a.method || '').localeCompare(b.method || '');
    });
  }, [endpoints, pathQuery, methodFilter, sortKey]);

  function exportCsv() {
    const header = ['id', 'method', 'route_pattern', 'content_type', 'auth_required'];
    const lines = [
      header.join(','),
      ...rows.map((e) =>
        [
          csvEscape(e.id),
          csvEscape(e.method || ''),
          csvEscape(e.route_pattern),
          csvEscape(e.content_type ?? ''),
          e.auth_required === null ? '' : e.auth_required ? 'true' : 'false',
        ].join(','),
      ),
    ];
    downloadBlob(
      `surface-${projectId.slice(0, 8)}.csv`,
      lines.join('\n'),
      'text/csv;charset=utf-8',
    );
  }

  function exportJson() {
    const payload = {
      project_id: projectId,
      project_name: projectName,
      exported_at: new Date().toISOString(),
      endpoint_count: rows.length,
      endpoints: rows,
    };
    downloadBlob(
      `surface-${projectId.slice(0, 8)}.json`,
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
            Path contains
            <input
              value={pathQuery}
              onChange={(e) => setPathQuery(e.target.value)}
              placeholder="/api/…"
              style={{ padding: 8, minWidth: 220 }}
            />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', fontSize: 13, gap: 4 }}>
            Method
            <select
              value={methodFilter}
              onChange={(e) => setMethodFilter(e.target.value)}
              style={{ padding: 8, minWidth: 120 }}
            >
              <option value="">All</option>
              {methods.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', fontSize: 13, gap: 4 }}>
            Sort
            <select
              value={sortKey}
              onChange={(e) => setSortKey(e.target.value as SortKey)}
              style={{ padding: 8, minWidth: 140 }}
            >
              <option value="path">Path A–Z</option>
              <option value="method">Method, then path</option>
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
          Showing <strong>{rows.length}</strong> of {endpoints.length} endpoints (client-side filter).
        </p>
      </section>

      {rows.length === 0 ? (
        <p style={{ color: '#666' }}>No endpoints match the current filters.</p>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14, minWidth: 640 }}>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '1px solid #ccc' }}>
                <th style={{ padding: 8 }}>Method</th>
                <th style={{ padding: 8 }}>Path</th>
                <th style={{ padding: 8 }}>Content-Type</th>
                <th style={{ padding: 8 }}>Auth</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((e) => (
                <tr key={e.id} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: 8, fontFamily: 'monospace', whiteSpace: 'nowrap' }}>
                    {e.method}
                  </td>
                  <td style={{ padding: 8, fontFamily: 'monospace', wordBreak: 'break-all' }}>
                    {e.route_pattern}
                  </td>
                  <td style={{ padding: 8, fontSize: 13, color: '#444' }}>
                    {e.content_type ?? '—'}
                  </td>
                  <td style={{ padding: 8, fontSize: 13 }}>
                    {e.auth_required === null ? '—' : e.auth_required ? 'yes' : 'no'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
