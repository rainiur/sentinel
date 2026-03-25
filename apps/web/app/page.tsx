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
        <li>API health: <strong>{health}</strong></li>
        <li>Core pages to build next: Projects, Surface, Hypotheses, Evidence, Learning, Research, Policies</li>
      </ul>
    </main>
  );
}
