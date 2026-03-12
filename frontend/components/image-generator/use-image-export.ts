import { useCallback, useRef } from 'react';

export function useImageExport(filename = 'social-image.png') {
  const captureRef = useRef<HTMLDivElement>(null);

  const exportImage = useCallback(async () => {
    if (!captureRef.current) return;

    const html2canvas = (await import('html2canvas')).default;
    const canvas = await html2canvas(captureRef.current, {
      useCORS: true,
      scale: 1,
      logging: false,
      backgroundColor: null,
    });

    const link = document.createElement('a');
    link.download = filename;
    link.href = canvas.toDataURL('image/png');
    link.click();
  }, [filename]);

  return { captureRef, exportImage };
}
