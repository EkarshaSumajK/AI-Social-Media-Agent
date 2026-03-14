'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  BarChart3,
  BookOpen,
  CalendarDays,
  Flame,
  Globe,
  Home,
  Lightbulb,
  LogOut,
  Megaphone,
  Moon,
  Newspaper,
  Repeat,
  Shield,
  Sun,
  Target,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Sidebar as UiSidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  SidebarSeparator,
  SidebarTrigger,
} from '@/components/ui/sidebar';
import { clearSession, getStoredUser } from '@/lib/auth';
import { useTheme } from '@/lib/theme';
import type { User } from '@/lib/types';
import { PLATFORMS } from '@/lib/types';
import { cn } from '@/lib/utils';

/** 10 main flows from platform spec (pdf1 + pdf2) */
const FLOWS = [
  { href: '/dashboard', label: 'Dashboard', icon: Home },
  { href: '/dashboard/flows/trending-post', label: 'Trending Now', icon: Flame },
  { href: '/dashboard/daily-posts', label: 'Daily Post Suggestions', icon: Newspaper },
  { href: '/dashboard/flows/webinar', label: 'Event / Webinar Builder', icon: Megaphone },
  { href: '/dashboard/thought-leadership', label: 'Thought Leadership', icon: Lightbulb },
  { href: '/dashboard/audience-content', label: 'Audience Content', icon: Target },
  { href: '/dashboard/platform-content', label: 'Platform Generator', icon: Globe },
  { href: '/dashboard/repurpose', label: 'Repurpose Content', icon: Repeat },
  { href: '/dashboard/scheduling', label: 'Automation & Scheduling', icon: CalendarDays },
  { href: '/dashboard/competitors', label: 'Competitor Insights', icon: Shield },
  { href: '/dashboard/performance', label: 'Performance Analytics', icon: BarChart3 },
  { href: '/dashboard/article-pipeline', label: 'Article Pipeline', icon: BookOpen },
] as const;

const PLATFORM_STYLES: Record<string, { dot: string; badge: string }> = {
  horizon: { dot: 'bg-cyan-400', badge: 'border-cyan-400/20 bg-cyan-400/10 text-cyan-500' },
  connect: { dot: 'bg-violet-400', badge: 'border-violet-400/20 bg-violet-400/10 text-violet-500' },
  parentshala: { dot: 'bg-pink-400', badge: 'border-pink-400/20 bg-pink-400/10 text-pink-500' },
};

export function Sidebar() {
  const pathname = usePathname();
  const user = getStoredUser<User>();
  const { theme, toggleTheme } = useTheme();
  const platformKey = user?.platform ?? 'horizon';
  const platformStyle = PLATFORM_STYLES[platformKey] ?? PLATFORM_STYLES.horizon;
  const currentPlatform = PLATFORMS.find((platform) => platform.value === platformKey) ?? PLATFORMS[0];

  function handleSignOut() {
    clearSession();
    window.location.href = '/login';
  }

  return (
    <UiSidebar collapsible="icon" className="border-r border-white/[0.06] bg-[#06080d] text-ink dark:bg-[#06080d]">
      <SidebarHeader className="gap-2 px-2 py-3">
        <div className="flex items-center gap-2.5">
          <div
            className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg border border-apple-blue/25 bg-apple-blue/10 text-xs font-bold text-apple-blue"
            style={{ fontFamily: 'var(--font-display)' }}
            title={currentPlatform.label}
          >
            {currentPlatform.label[0].toUpperCase()}
          </div>
          <div className="min-w-0 flex-1 group-data-[collapsible=icon]:hidden">
            <p className="truncate text-[13px] font-semibold text-ink" style={{ fontFamily: 'var(--font-display)' }}>
              {currentPlatform.label}
            </p>
            <Badge variant="outline" className={cn('mt-1 w-fit gap-1 border px-1.5 py-0 text-[9px] uppercase tracking-wider', platformStyle.badge)}>
              <span className={cn('h-1 w-1 rounded-full', platformStyle.dot)} />
              live
            </Badge>
          </div>
          <SidebarTrigger className="h-8 w-8 text-ink-faint hover:bg-white/[0.06] hover:text-ink group-data-[collapsible=icon]:mx-auto" />
        </div>
      </SidebarHeader>

      <SidebarSeparator className="mx-0 bg-white/[0.06]" />

      <SidebarContent className="px-2 py-2">
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-0.5">
              {FLOWS.map((item) => {
                const Icon = item.icon;
                const isActive = item.href === '/dashboard' ? pathname === '/dashboard' : pathname.startsWith(item.href);
                return (
                  <SidebarMenuItem key={item.href}>
                    <SidebarMenuButton
                      asChild
                      isActive={isActive}
                      tooltip={item.label}
                      className={cn(
                        'h-9 rounded-md px-2.5 text-[13px] text-ink-soft hover:bg-white/[0.05] hover:text-ink',
                        isActive && 'bg-apple-blue/10 font-semibold text-apple-blue hover:bg-apple-blue/15 hover:text-apple-blue',
                      )}
                    >
                      <Link href={item.href}>
                        <Icon size={15} className={cn('shrink-0', isActive ? 'text-apple-blue' : 'text-ink-faint')} />
                        <span>{item.label}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarSeparator className="mx-0 bg-white/[0.06]" />

      <SidebarFooter className="gap-2 px-2 py-3">
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleTheme}
          className="h-8 w-full justify-start text-[12px] text-ink-soft hover:bg-white/[0.05] hover:text-ink group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:px-0"
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
          <span className="group-data-[collapsible=icon]:hidden">{theme === 'dark' ? 'Light mode' : 'Dark mode'}</span>
          <Badge variant="secondary" className="ml-auto px-1.5 py-0 text-[10px] font-medium capitalize group-data-[collapsible=icon]:hidden">
            {theme}
          </Badge>
        </Button>

        <div className="flex items-center gap-2 px-1 group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:px-0" title={user?.full_name ?? 'User'}>
          <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full border border-white/[0.08] bg-white/[0.04] text-[10px] font-bold text-ink-soft">
            {(user?.full_name?.[0] ?? 'U').toUpperCase()}
          </div>
          <div className="min-w-0 group-data-[collapsible=icon]:hidden">
            <p className="truncate text-[12px] font-medium text-ink-soft">{user?.full_name ?? 'User'}</p>
            <p className="truncate text-[10px] capitalize text-ink-faint">{user?.role ?? 'reviewer'}</p>
          </div>
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={handleSignOut}
          className="h-8 w-full justify-start text-[12px] text-ink-faint hover:bg-red-500/10 hover:text-red-400 group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:px-0"
          title="Sign out"
        >
          <LogOut size={14} />
          <span className="group-data-[collapsible=icon]:hidden">Sign out</span>
        </Button>
      </SidebarFooter>

      <SidebarRail />
    </UiSidebar>
  );
}
