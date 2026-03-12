"use client";

import { useRouter } from "next/navigation";
import {
  BarChart3,
  BookOpen,
  Flame,
  Globe,
  LayoutDashboard,
  Lightbulb,
  Megaphone,
  Moon,
  Newspaper,
  PenTool,
  Repeat,
  Search,
  Send,
  Shield,
  Sparkles,
  Sun,
  Target,
  Trophy,
  Zap,
} from "lucide-react";

import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import { useTheme } from "@/lib/theme";

interface CommandMenuProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const navigationItems = [
  { label: "Command Center", href: "/dashboard", icon: LayoutDashboard },
  { label: "Topics Pipeline", href: "/dashboard/topics", icon: Search },
  { label: "Draft Queue", href: "/dashboard/drafts", icon: PenTool },
  { label: "Published", href: "/dashboard/published", icon: Send },
  { label: "Daily Posts", href: "/dashboard/daily-posts", icon: Newspaper },
  { label: "Thought Leadership", href: "/dashboard/thought-leadership", icon: Lightbulb },
  { label: "Audience Content", href: "/dashboard/audience-content", icon: Target },
  { label: "Platform Generator", href: "/dashboard/platform-content", icon: Globe },
  { label: "Campaigns", href: "/dashboard/campaigns", icon: Megaphone },
  { label: "Competitors", href: "/dashboard/competitors", icon: Shield },
  { label: "Hook Library", href: "/dashboard/hooks", icon: Flame },
  { label: "Swipe Files", href: "/dashboard/swipe-files", icon: BookOpen },
  { label: "Paraphraser", href: "/dashboard/paraphraser", icon: Sparkles },
  { label: "Content Scoring", href: "/dashboard/scoring", icon: Trophy },
  { label: "Performance", href: "/dashboard/performance", icon: BarChart3 },
  { label: "Audit Log", href: "/dashboard/audit", icon: Zap },
];

const actionItems = [
  { label: "Repurpose Content", href: "/dashboard/repurpose", icon: Repeat },
];

export function CommandMenu({ open, onOpenChange }: CommandMenuProps) {
  const router = useRouter();
  const { theme, toggle } = useTheme();

  function runCommand(command: () => void) {
    onOpenChange(false);
    command();
  }

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder="Type a command or search..." />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>

        <CommandGroup heading="Navigation">
          {navigationItems.map((item) => (
            <CommandItem
              key={item.href}
              className="flex items-center gap-2"
              onSelect={() => runCommand(() => router.push(item.href))}
            >
              <item.icon size={16} className="text-ink-soft" />
              <span>{item.label}</span>
            </CommandItem>
          ))}
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Actions">
          {actionItems.map((item) => (
            <CommandItem
              key={item.href}
              className="flex items-center gap-2"
              onSelect={() => runCommand(() => router.push(item.href))}
            >
              <item.icon size={16} className="text-ink-soft" />
              <span>{item.label}</span>
            </CommandItem>
          ))}
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Settings">
          <CommandItem
            className="flex items-center gap-2"
            onSelect={() => runCommand(toggle)}
          >
            {theme === "dark" ? (
              <Sun size={16} className="text-ink-soft" />
            ) : (
              <Moon size={16} className="text-ink-soft" />
            )}
            <span>Toggle Theme</span>
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
