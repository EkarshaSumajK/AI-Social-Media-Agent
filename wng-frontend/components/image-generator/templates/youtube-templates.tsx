import type { TemplateProps } from '../types';

const W = 1280;
const H = 720;
const FONT = '"Inter", system-ui, -apple-system, sans-serif';
const TEXT = '#ffffff';
const MUTED = 'rgba(255,255,255,0.6)';

function Base({ containerRef, children, bg }: {
  containerRef?: React.Ref<HTMLDivElement>;
  children: React.ReactNode;
  bg: string;
}) {
  return (
    <div
      ref={containerRef}
      style={{ width: W, height: H, background: bg, fontFamily: FONT, color: TEXT,
        position: 'relative', overflow: 'hidden', boxSizing: 'border-box' }}
    >
      {children}
    </div>
  );
}

function YTBadge({ label }: { label: string }) {
  return (
    <div style={{ position: 'absolute', top: 36, right: 44,
      background: '#ff0000', borderRadius: 8, padding: '6px 16px',
      fontSize: 18, fontWeight: 800, color: TEXT }}>
      ▶ YouTube
    </div>
  );
}

// ─── 1. Number List ───────────────────────────────────────────────────────────
export function NumberList({ content, brandName, containerRef }: TemplateProps) {
  const firstLine = content.split('\n')[0] || content.slice(0, 80);
  const numMatch = content.match(/\b(\d+)\b/);
  const num = numMatch ? numMatch[1] : '5';

  return (
    <Base containerRef={containerRef} bg="linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%)">
      <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 8, background: '#ff0000' }} />
      <div style={{ position: 'absolute', right: -80, top: -80, width: 400, height: 400,
        borderRadius: '50%', background: 'rgba(255,0,0,0.08)' }} />
      <YTBadge label="YouTube" />
      <div style={{ padding: '60px 80px', display: 'flex', alignItems: 'center', height: '100%' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 52 }}>
          <div style={{ fontSize: 180, fontWeight: 900, color: '#ff0000', lineHeight: 1,
            textShadow: '0 0 60px rgba(255,0,0,0.4)', flexShrink: 0, width: 220 }}>
            {num}
          </div>
          <div>
            <div style={{ fontSize: 18, fontWeight: 800, color: MUTED, letterSpacing: 3,
              textTransform: 'uppercase', marginBottom: 16 }}>Things You Need to Know</div>
            <p style={{ fontSize: 38, fontWeight: 800, color: TEXT, margin: 0, lineHeight: 1.3,
              display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
              {firstLine}
            </p>
          </div>
        </div>
      </div>
    </Base>
  );
}

// ─── 2. Warning Thumbnail ─────────────────────────────────────────────────────
export function WarningThumbnail({ content, brandName, containerRef }: TemplateProps) {
  const firstLine = content.split('\n')[0] || content.slice(0, 70);
  return (
    <Base containerRef={containerRef} bg="linear-gradient(135deg, #1a0000 0%, #2d0000 100%)">
      <div style={{ position: 'absolute', inset: 0,
        backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 40px, rgba(255,0,0,0.03) 40px, rgba(255,0,0,0.03) 80px)' }} />
      <YTBadge label="YouTube" />
      <div style={{ padding: '60px 80px', display: 'flex', alignItems: 'center', height: '100%' }}>
        <div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 12,
            background: '#ff000020', border: '2px solid #ff000040',
            borderRadius: 12, padding: '8px 20px', marginBottom: 28 }}>
            <span style={{ fontSize: 24 }}>⚠️</span>
            <span style={{ color: '#ff6b6b', fontSize: 20, fontWeight: 800, letterSpacing: 2, textTransform: 'uppercase' }}>Warning</span>
          </div>
          <p style={{ fontSize: 52, fontWeight: 900, color: TEXT, margin: 0, lineHeight: 1.2,
            maxWidth: 1000,
            display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
            {firstLine}
          </p>
        </div>
      </div>
    </Base>
  );
}

// ─── 3. Myth Busting ──────────────────────────────────────────────────────────
export function MythBusting({ content, brandName, containerRef }: TemplateProps) {
  const firstLine = content.split('\n')[0] || content.slice(0, 70);
  return (
    <Base containerRef={containerRef} bg="linear-gradient(135deg, #0d1117 0%, #1a2030 100%)">
      <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 8,
        background: 'linear-gradient(180deg, #ff0000, #ff6b6b)' }} />
      <YTBadge label="YouTube" />
      <div style={{ padding: '60px 80px', display: 'flex', flexDirection: 'column',
        justifyContent: 'center', height: '100%' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 20, marginBottom: 28 }}>
          <div style={{ background: '#ff000020', border: '2px solid #ff000050',
            borderRadius: 14, padding: '10px 20px', fontSize: 20, fontWeight: 800,
            color: '#ff6b6b', letterSpacing: 1, textTransform: 'uppercase' }}>
            🚫 MYTH BUSTED
          </div>
        </div>
        <p style={{ fontSize: 50, fontWeight: 900, color: TEXT, margin: 0, lineHeight: 1.25,
          maxWidth: 1000,
          display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {firstLine}
        </p>
        <div style={{ marginTop: 28, fontSize: 22, color: MUTED }}>Watch to find out the truth 👇</div>
      </div>
    </Base>
  );
}

// ─── 4. Symptoms Guide ────────────────────────────────────────────────────────
export function SymptomsGuide({ content, brandName, containerRef }: TemplateProps) {
  const lines = content.split('\n').map(l => l.replace(/^[-•*\d.]+\s*/, '').trim()).filter(Boolean);
  const items = lines.length > 1 ? lines : content.split(/[.!?]/).map(s => s.trim()).filter(Boolean);
  const shown = items.slice(0, 4);

  return (
    <Base containerRef={containerRef} bg="linear-gradient(135deg, #0a1628 0%, #0d1f3c 100%)">
      <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 8, background: '#3b82f6' }} />
      <YTBadge label="YouTube" />
      <div style={{ padding: '50px 80px', display: 'flex', height: '100%', flexDirection: 'column',
        justifyContent: 'center' }}>
        <div style={{ fontSize: 22, fontWeight: 800, color: '#60a5fa', letterSpacing: 2,
          textTransform: 'uppercase', marginBottom: 28 }}>🩺 Symptoms Guide</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {shown.map((item, i) => (
            <div key={i} style={{ background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.25)',
              borderRadius: 14, padding: '16px 20px', display: 'flex', alignItems: 'flex-start', gap: 12 }}>
              <span style={{ color: '#60a5fa', fontWeight: 800, fontSize: 18, flexShrink: 0 }}>{i + 1}.</span>
              <p style={{ fontSize: 22, lineHeight: 1.4, color: TEXT, margin: 0,
                display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                {item}
              </p>
            </div>
          ))}
        </div>
      </div>
    </Base>
  );
}

// ─── 5. Doctor Explains ───────────────────────────────────────────────────────
export function DoctorExplains({ content, brandName, containerRef }: TemplateProps) {
  const firstLine = content.split('\n')[0] || content.slice(0, 80);
  return (
    <Base containerRef={containerRef} bg="linear-gradient(135deg, #0a1a0a 0%, #0d2010 100%)">
      <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 8, background: '#22c55e' }} />
      <YTBadge label="YouTube" />
      <div style={{ padding: '60px 80px', display: 'flex', alignItems: 'center', height: '100%' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 28 }}>
            <span style={{ fontSize: 44 }}>👨‍⚕️</span>
            <div>
              <div style={{ color: '#22c55e', fontSize: 22, fontWeight: 800, letterSpacing: 2, textTransform: 'uppercase' }}>Doctor Explains</div>
              <div style={{ color: MUTED, fontSize: 18, marginTop: 4 }}>Medical Insights</div>
            </div>
          </div>
          <p style={{ fontSize: 50, fontWeight: 900, color: TEXT, margin: 0, lineHeight: 1.25,
            maxWidth: 1000,
            display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
            {firstLine}
          </p>
        </div>
      </div>
    </Base>
  );
}

// ─── 6. Before vs After ───────────────────────────────────────────────────────
export function BeforeVsAfter({ content, brandName, containerRef }: TemplateProps) {
  const half = Math.floor(content.length / 2);
  const before = content.slice(0, half).trim();
  const after = content.slice(half).trim();

  return (
    <Base containerRef={containerRef} bg="#0f0f0f">
      <YTBadge label="YouTube" />
      <div style={{ display: 'flex', height: '100%' }}>
        <div style={{ flex: 1, background: 'rgba(239,68,68,0.08)', padding: '60px 50px 60px 80px',
          borderRight: '4px solid #333', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <div style={{ fontSize: 22, fontWeight: 800, color: '#ef4444', letterSpacing: 2,
            textTransform: 'uppercase', marginBottom: 20 }}>❌ Before</div>
          <p style={{ fontSize: 28, lineHeight: 1.5, color: '#fca5a5', margin: 0,
            display: '-webkit-box', WebkitLineClamp: 5, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
            {before}
          </p>
        </div>
        <div style={{ flex: 1, background: 'rgba(34,197,94,0.08)', padding: '60px 80px 60px 50px',
          display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <div style={{ fontSize: 22, fontWeight: 800, color: '#22c55e', letterSpacing: 2,
            textTransform: 'uppercase', marginBottom: 20 }}>✅ After</div>
          <p style={{ fontSize: 28, lineHeight: 1.5, color: '#86efac', margin: 0,
            display: '-webkit-box', WebkitLineClamp: 5, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
            {after}
          </p>
        </div>
      </div>
    </Base>
  );
}

// ─── 7. Top Mistakes ──────────────────────────────────────────────────────────
export function TopMistakes({ content, brandName, containerRef }: TemplateProps) {
  const firstLine = content.split('\n')[0] || content.slice(0, 70);
  return (
    <Base containerRef={containerRef} bg="linear-gradient(135deg, #1a0d00 0%, #2d1a00 100%)">
      <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 8, background: '#f59e0b' }} />
      <YTBadge label="YouTube" />
      <div style={{ padding: '60px 80px', display: 'flex', flexDirection: 'column',
        justifyContent: 'center', height: '100%' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 12,
          background: '#f59e0b15', border: '2px solid #f59e0b30',
          borderRadius: 12, padding: '8px 20px', marginBottom: 28, width: 'fit-content' }}>
          <span style={{ fontSize: 22 }}>🚨</span>
          <span style={{ color: '#f59e0b', fontSize: 20, fontWeight: 800, letterSpacing: 2, textTransform: 'uppercase' }}>Common Mistakes</span>
        </div>
        <p style={{ fontSize: 52, fontWeight: 900, color: TEXT, margin: 0, lineHeight: 1.2,
          maxWidth: 1000,
          display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {firstLine}
        </p>
        <div style={{ marginTop: 28, fontSize: 22, color: MUTED }}>Are you making these? Watch now 👇</div>
      </div>
    </Base>
  );
}
