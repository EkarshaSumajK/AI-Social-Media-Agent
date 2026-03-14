'use client';

import { AuthGuard } from '@/components/auth-guard';
import { DashboardBreadcrumbs } from '@/components/dashboard-breadcrumbs';
import { Sidebar } from '@/components/sidebar';
import { SidebarInset, SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <SidebarProvider
        style={
          {
            '--sidebar-width': '15.75rem',
            '--sidebar-width-icon': '4.75rem',
          } as React.CSSProperties
        }
      >
        <Sidebar />
        <SidebarInset className="flex flex-col overflow-y-auto" style={{ background: 'var(--app-bg)', transition: 'background 0.2s ease' }}>
          <header className="sticky top-0 z-30 flex shrink-0 flex-col gap-2 border-b border-white/[0.06] bg-canvas/80 px-4 py-3 backdrop-blur-md sm:px-6">
            <div className="flex items-center justify-between gap-2">
              <DashboardBreadcrumbs />
              <SidebarTrigger className="h-8 w-8 shrink-0 md:hidden" />
            </div>
          </header>
          <main className="min-h-0 flex-1">{children}</main>
        </SidebarInset>
      </SidebarProvider>
    </AuthGuard>
  );
}
