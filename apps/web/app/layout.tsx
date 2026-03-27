import type { Metadata } from 'next';
import Link from 'next/link';
import type { ReactNode } from 'react';

export const metadata: Metadata = {
  title: 'Sentinel for Caido',
  description: 'Authorized testing assistant control plane',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <nav
          style={{
            padding: '12px 32px',
            borderBottom: '1px solid #e5e5e5',
            fontFamily: 'system-ui, sans-serif',
            fontSize: 14,
          }}
        >
          <Link href="/">Home</Link>
          <span style={{ margin: '0 10px', color: '#ccc' }}>|</span>
          <Link href="/dashboard">Dashboard</Link>
          <span style={{ margin: '0 10px', color: '#ccc' }}>|</span>
          <Link href="/projects">Projects</Link>
          <span style={{ margin: '0 10px', color: '#ccc' }}>|</span>
          <Link href="/admin">Admin</Link>
        </nav>
        {children}
      </body>
    </html>
  );
}
