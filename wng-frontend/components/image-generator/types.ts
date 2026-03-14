import type React from 'react';

export type Platform = 'twitter' | 'linkedin' | 'instagram' | 'threads' | 'youtube';

export interface TemplateProps {
  content: string;
  platform: Platform;
  brandName?: string;
  containerRef?: React.Ref<HTMLDivElement>;
}

export interface TemplateConfig {
  id: string;
  label: string;
  width: number;
  height: number;
  component: React.ComponentType<TemplateProps>;
}

export type TemplateRegistry = Record<Platform, TemplateConfig[]>;
