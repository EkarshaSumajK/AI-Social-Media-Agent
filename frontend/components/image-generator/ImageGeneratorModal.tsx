'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { Check, Cloud, Download, ImageIcon, Loader2, RefreshCw } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { extractImageText, uploadImage } from '@/lib/api';
import { cn } from '@/lib/utils';

import { CONTENT_TYPE_DEFAULT, TEMPLATE_REGISTRY } from './template-registry';
import type { Platform, TemplateConfig } from './types';

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  content: string;
  platform: Platform;
  contentType?: string;
  brandName?: string;
}

// Maximum preview width inside the modal
const PREVIEW_MAX_W = 520;

export function ImageGeneratorModal({ open, onOpenChange, content, platform, contentType, brandName }: Props) {
  const templates = TEMPLATE_REGISTRY[platform] ?? [];

  // Pick a smart default template based on content type
  const defaultId =
    (contentType && CONTENT_TYPE_DEFAULT[platform]?.[contentType]) ??
    templates[0]?.id ?? '';

  const [selectedId, setSelectedId] = useState<string>(defaultId);
  const [exporting, setExporting] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadedUrl, setUploadedUrl] = useState<string | null>(null);
  const [imageText, setImageText] = useState<string>('');
  const [extracting, setExtracting] = useState(false);

  // Update default when modal opens with new props
  const resolvedId = selectedId || defaultId;
  const template = templates.find((t) => t.id === resolvedId) ?? templates[0];

  // Fetch extracted text when modal opens or template changes
  useEffect(() => {
    if (!open || !template) return;
    let cancelled = false;
    setExtracting(true);
    extractImageText({ content, platform, template_type: template.id })
      .then((res) => { if (!cancelled) setImageText(res.image_text); })
      .catch(() => { if (!cancelled) setImageText(content.slice(0, 200)); })
      .finally(() => { if (!cancelled) setExtracting(false); });
    return () => { cancelled = true; };
  }, [open, template?.id, content, platform]);

  // Ref points to the hidden full-size element for capture
  const captureRef = useRef<HTMLDivElement>(null);

  const scale = template ? PREVIEW_MAX_W / template.width : 1;
  const previewH = template ? Math.round(template.height * scale) : 300;

  const handleExport = useCallback(async () => {
    if (!captureRef.current || !template) return;
    setExporting(true);
    try {
      const html2canvas = (await import('html2canvas')).default;
      const canvas = await html2canvas(captureRef.current, {
        useCORS: true,
        scale: 1,
        logging: false,
        backgroundColor: null,
        width: template.width,
        height: template.height,
      });
      const link = document.createElement('a');
      link.download = `${platform}-${template.id}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    } finally {
      setExporting(false);
    }
  }, [platform, template]);

  const handleUpload = useCallback(async () => {
    if (!captureRef.current || !template) return;
    setUploading(true);
    try {
      const html2canvas = (await import('html2canvas')).default;
      const canvas = await html2canvas(captureRef.current, {
        useCORS: true,
        scale: 1,
        logging: false,
        backgroundColor: null,
        width: template.width,
        height: template.height,
      });
      const dataUrl = canvas.toDataURL('image/png');
      const result = await uploadImage(dataUrl);
      setUploadedUrl(result.url);
      await navigator.clipboard.writeText(result.url);
    } finally {
      setUploading(false);
    }
  }, [template]);

  if (!template) return null;

  const TemplateComponent = template.component;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[620px] p-0 gap-0 overflow-hidden">
        <DialogHeader className="px-6 py-4 border-b border-white/[0.06]">
          <DialogTitle className="flex items-center gap-2 text-base">
            <ImageIcon size={16} className="text-apple-blue" />
            Generate Image
            <span className="ml-auto rounded-full border border-white/[0.08] bg-white/[0.04] px-2.5 py-0.5 text-xs text-ink-soft capitalize">
              {platform === 'twitter' ? 'X / Twitter' : platform}
            </span>
          </DialogTitle>
        </DialogHeader>

        {/* Template selector */}
        <div className="px-6 pt-4 pb-2">
          <p className="mb-2 text-xs font-medium text-ink-soft">Choose a template</p>
          <div className="flex flex-wrap gap-2">
            {templates.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setSelectedId(t.id)}
                className={cn(
                  'rounded-full border px-3 py-1 text-xs font-medium transition-colors',
                  resolvedId === t.id
                    ? 'border-apple-blue/60 bg-apple-blue/15 text-apple-blue'
                    : 'border-white/[0.08] bg-white/[0.03] text-ink-soft hover:border-apple-blue/30 hover:text-ink',
                )}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Preview */}
        <div className="px-6 py-4">
          <p className="mb-2 text-xs font-medium text-ink-soft">Preview</p>
          <div
            className="relative overflow-hidden rounded-xl border border-white/[0.06]"
            style={{ width: PREVIEW_MAX_W, height: previewH }}
          >
            <div style={{ transform: `scale(${scale})`, transformOrigin: 'top left', pointerEvents: 'none' }}>
              <TemplateComponent content={imageText || content} platform={platform} brandName={brandName} />
            </div>
            {extracting && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                <Loader2 size={24} className="animate-spin text-apple-blue" />
              </div>
            )}
          </div>
        </div>

        {/* Hidden full-size element for html2canvas capture */}
        <div style={{ position: 'fixed', top: '-99999px', left: '-99999px', zIndex: -1 }}>
          <TemplateComponent
            content={imageText || content}
            platform={platform}
            brandName={brandName}
            containerRef={captureRef}
          />
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between gap-3 border-t border-white/[0.06] px-6 py-4">
          <p className="text-xs text-ink-faint">
            {template.width} × {template.height}px
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                const idx = templates.findIndex((t) => t.id === resolvedId);
                const next = templates[(idx + 1) % templates.length];
                setSelectedId(next.id);
              }}
            >
              <RefreshCw size={14} className="mr-1.5" />
              Next template
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleUpload}
              disabled={uploading || extracting}
              title="Upload to Cloudinary and copy URL to clipboard"
            >
              {uploading ? (
                <><Loader2 size={14} className="mr-1.5 animate-spin" />Uploading...</>
              ) : uploadedUrl ? (
                <><Check size={14} className="mr-1.5 text-emerald-400" />URL Copied!</>
              ) : (
                <><Cloud size={14} className="mr-1.5" />Upload & Copy URL</>
              )}
            </Button>
            <Button size="sm" onClick={handleExport} disabled={exporting || extracting}>
              {exporting ? (
                <>
                  <Loader2 size={14} className="mr-1.5 animate-spin" />
                  Exporting...
                </>
              ) : (
                <>
                  <Download size={14} className="mr-1.5" />
                  Download PNG
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
