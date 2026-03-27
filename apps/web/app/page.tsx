import Link from 'next/link';

async function getHealth(): Promise<string> {
  try {
    const base = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080';
    const res = await fetch(`${base}/health`, { cache: 'no-store' });
    const json = await res.json();
    return json.status || 'unknown';
  } catch {
    return 'unreachable';
  }
}

export default async function Page() {
  const health = await getHealth();

  return (
    <main style={{ fontFamily: 'Arial, sans-serif', padding: 32 }}>
      <h1>Sentinel for Caido</h1>
      <p>Authorized testing assistant control plane.</p>
      <ul>
        <li>
          API health: <strong>{health}</strong>
        </li>
        <li>
          <Link href="/dashboard">Dashboard</Link> — health, version, project count, MCP summary
        </li>
        <li>
          <Link href="/admin">Admin</Link> — policy / ops flags, MCP summary, doc pointers
        </li>
        <li>
          <Link href="/projects">Projects</Link> — list, surface inventory (filters/export), hypotheses, findings,
          evidence
        </li>
        <li>Still to build: Learning, Research, Policies (richer analyst UX)</li>
      </ul>
    </main>
  );
}
