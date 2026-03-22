import type { Metadata } from 'next';

import { ThemeProvider } from '@/lib/theme';
import './globals.css';

export const metadata: Metadata = {
  title: 'Wellnest Intelligent Marketing (WIM)',
  description: 'AI-powered content operations — Horizon · Connect · Parentshala',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    // suppressHydrationWarning prevents mismatch when ThemeProvider adds
    // .dark / .light class on the client after reading localStorage.
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
