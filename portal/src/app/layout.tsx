import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'LocalMind Portal',
  description: 'Your AI, Offline',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
