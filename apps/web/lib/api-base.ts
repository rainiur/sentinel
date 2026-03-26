/** Browser and server: same env as Docker Compose / local dev (see README). */
export function getApiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (raw && raw.length > 0) {
    return raw.replace(/\/$/, '');
  }
  return 'http://localhost:8080';
}
