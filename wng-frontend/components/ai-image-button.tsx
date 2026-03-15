'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { generateAIImageFromText } from '@/lib/api';

const PLATFORM_LABELS: Record<string, string> = {
  instagram: '📸 Instagram (1080×1080)',
  linkedin: '💼 LinkedIn (1200×627)',
  twitter: '🐦 Twitter/X (1600×900)',
  facebook: '👥 Facebook (1200×630)',
};

interface AIImageButtonProps {
  caption: string;
  platform: string;
  title?: string;
  context?: string;
  onGenerated?: (imageUrl: string) => void;
}

export function AIImageButton({ caption, platform, title, context, onGenerated }: AIImageButtonProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [previewImage, setPreviewImage] = useState<string | null>(null);

  const handleGenerate = async () => {
    setLoading(true);
    setError('');
    try {
      const result = await generateAIImageFromText({
        caption,
        platform,
        title: title || '',
        context: context || '',
      });
      setPreviewImage(result.image_url);
      onGenerated?.(result.image_url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate image');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="flex items-center gap-2">
        <Button
          size="sm"
          variant="outline"
          onClick={handleGenerate}
          disabled={loading || !caption.trim()}
        >
          {loading ? 'Generating...' : previewImage ? 'Regenerate Image' : 'Generate AI Image'}
        </Button>
        <span className="text-xs text-muted-foreground">{PLATFORM_LABELS[platform] || platform}</span>
        {previewImage && (
          <Button size="sm" variant="ghost" onClick={() => setPreviewImage(previewImage)}>
            Preview
          </Button>
        )}
      </div>

      {error && <p className="mt-1 text-xs text-red-500">{error}</p>}

      <Dialog open={!!previewImage} onOpenChange={(open) => !open && setPreviewImage(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="capitalize">{platform} — AI Generated Infographic</DialogTitle>
            <DialogDescription>
              {PLATFORM_LABELS[platform] || 'Generated with gpt-image-1'}
            </DialogDescription>
          </DialogHeader>
          {previewImage && (
            <div className="flex flex-col items-center gap-3">
              <img
                src={previewImage}
                alt={`${platform} AI infographic`}
                className="rounded-lg border max-w-full max-h-[60vh] object-contain"
              />
              <div className="flex gap-2">
                <a href={previewImage} target="_blank" rel="noopener noreferrer">
                  <Button size="sm" variant="outline">Open Full Image</Button>
                </a>
                <a href={previewImage} download={`${platform}-infographic.png`}>
                  <Button size="sm" variant="outline">Download</Button>
                </a>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
