import type { TemplateProps } from '../types';

const W = 1080;
const H = 1080;
const FONT = '"Inter", system-ui, -apple-system, sans-serif';
const TEXT = '#ffffff';
const MUTED = 'rgba(255,255,255,0.65)';

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

function Footer({ brand, label }: { brand?: string; label?: string }) {
  return (
    <div style={{ position: 'absolute', bottom: 48, left: 64, right: 64,
      display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <span style={{ color: MUTED, fontSize: 24 }}>{brand ?? '@YourBrand'}</span>
      {label && <span style={{ color: MUTED, fontSize: 22, fontWeight: 600 }}>{label}</span>}
    </div>
  );
}

// ─── 1. Carousel Cover ────────────────────────────────────────────────────────
export function CarouselCover({ content, brandName, containerRef }: TemplateProps) {
  const firstLine = content.split('\n')[0] || content.slice(0, 60);
  return (
    <Base containerRef={containerRef} bg="linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)">
      <div style={{ position: 'absolute', top: -100, right: -100, width: 400, height: 400,
        borderRadius: '50%', background: 'rgba(233,30,99,0.15)' }} />
      <div style={{ position: 'absolute', bottom: -80, left: -80, width: 320, height: 320,
        borderRadius: '50%', background: 'rgba(103,58,183,0.15)' }} />
      <div style={{ padding: '80px 64px', display: 'flex', flexDirection: 'column',
        height: '100%', justifyContent: 'center' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10,
          background: 'rgba(233,30,99,0.25)', border: '1px solid rgba(233,30,99,0.5)',
          borderRadius: 30, padding: '8px 20px', marginBottom: 40, width: 'fit-content' }}>
          <span style={{ color: '#f48fb1', fontSize: 18, fontWeight: 700, letterSpacing: 2, textTransform: 'uppercase' }}>📖 Read More</span>
        </div>
        <p style={{ fontSize: 52, fontWeight: 800, lineHeight: 1.3, color: TEXT,
          display: '-webkit-box', WebkitLineClamp: 4, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {firstLine}
        </p>
        <div style={{ marginTop: 40, display: 'flex', alignItems: 'center', gap: 12 }}>
          {[1,2,3,4,5].map(n => (
            <div key={n} style={{ width: n === 1 ? 32 : 10, height: 10, borderRadius: 5,
              background: n === 1 ? '#e91e63' : 'rgba(255,255,255,0.3)' }} />
          ))}
        </div>
      </div>
      <Footer brand={brandName} />
    </Base>
  );
}

// ─── 2. Health Tips ───────────────────────────────────────────────────────────
export function HealthTips({ content, brandName, containerRef }: TemplateProps) {
  const lines = content.split('\n').map(l => l.replace(/^[-•*\d.]+\s*/, '').trim()).filter(Boolean);
  const items = lines.length > 1 ? lines : content.split(/[.!?]/).map(s => s.trim()).filter(Boolean);
  const shown = items.slice(0, 5);

  return (
    <Base containerRef={containerRef} bg="linear-gradient(160deg, #0d4a3a 0%, #145a42 60%, #1a6b4f 100%)">
      <div style={{ position: 'absolute', top: -60, right: -60, width: 280, height: 280,
        borderRadius: '50%', background: 'rgba(52,211,153,0.12)' }} />
      <div style={{ padding: '64px 64px 120px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 44 }}>
          <span style={{ fontSize: 44 }}>💚</span>
          <div>
            <div style={{ fontSize: 32, fontWeight: 800, color: '#6ee7b7' }}>Health Tips</div>
            <div style={{ fontSize: 20, color: MUTED, marginTop: 4 }}>For a healthier you</div>
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {shown.map((item, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 20 }}>
              <div style={{ width: 36, height: 36, borderRadius: 10, background: '#34d39920',
                border: '1px solid #34d39940', display: 'flex', alignItems: 'center',
                justifyContent: 'center', flexShrink: 0, marginTop: 4 }}>
                <span style={{ color: '#34d399', fontWeight: 800, fontSize: 16 }}>{i + 1}</span>
              </div>
              <p style={{ fontSize: 28, lineHeight: 1.5, color: TEXT, margin: 0,
                display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                {item}
              </p>
            </div>
          ))}
        </div>
      </div>
      <Footer brand={brandName} label="Instagram" />
    </Base>
  );
}

// ─── 3. Symptoms Explainer ────────────────────────────────────────────────────
export function SymptomsExplainer({ content, brandName, containerRef }: TemplateProps) {
  const lines = content.split('\n').map(l => l.replace(/^[-•*\d.]+\s*/, '').trim()).filter(Boolean);
  const items = lines.length > 1 ? lines : content.split(/[.!?]/).map(s => s.trim()).filter(Boolean);
  const shown = items.slice(0, 5);

  return (
    <Base containerRef={containerRef} bg="linear-gradient(145deg, #1a0533 0%, #2d0a4e 60%, #1a0533 100%)">
      <div style={{ position: 'absolute', inset: 0,
        backgroundImage: 'radial-gradient(circle at 80% 20%, rgba(168,85,247,0.15) 0%, transparent 50%)' }} />
      <div style={{ padding: '64px 64px 120px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 44 }}>
          <span style={{ fontSize: 44 }}>🩺</span>
          <div>
            <div style={{ fontSize: 32, fontWeight: 800, color: '#c084fc' }}>Symptoms to Know</div>
            <div style={{ fontSize: 20, color: MUTED, marginTop: 4 }}>Early detection matters</div>
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {shown.map((item, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 18,
              background: 'rgba(168,85,247,0.1)', border: '1px solid rgba(168,85,247,0.2)',
              borderRadius: 14, padding: '16px 24px' }}>
              <span style={{ fontSize: 22, flexShrink: 0 }}>⚠️</span>
              <p style={{ fontSize: 26, lineHeight: 1.4, color: TEXT, margin: 0,
                display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                {item}
              </p>
            </div>
          ))}
        </div>
      </div>
      <Footer brand={brandName} label="Instagram" />
    </Base>
  );
}

// ─── 4. Do vs Don't ───────────────────────────────────────────────────────────
export function DoVsDont({ content, brandName, containerRef }: TemplateProps) {
  const doMatch = content.match(/do[:\s]+(.+?)(?=don'?t[:\s]|$)/is);
  const dontMatch = content.match(/don'?t[:\s]+(.+)/is);
  const half = Math.floor(content.length / 2);
  const doText = doMatch ? doMatch[1].trim() : content.slice(0, half).trim();
  const dontText = dontMatch ? dontMatch[1].trim() : content.slice(half).trim();

  return (
    <Base containerRef={containerRef} bg="#0d1117">
      <div style={{ padding: '64px 48px 120px' }}>
        <div style={{ textAlign: 'center', fontSize: 38, fontWeight: 900, marginBottom: 44,
          letterSpacing: 1 }}>DO's <span style={{ color: '#71767b' }}>vs</span> DON'Ts</div>
        <div style={{ display: 'flex', gap: 24 }}>
          <div style={{ flex: 1, background: 'rgba(34,197,94,0.08)', border: '2px solid rgba(34,197,94,0.3)',
            borderRadius: 20, padding: '32px' }}>
            <div style={{ fontSize: 28, fontWeight: 800, color: '#22c55e', marginBottom: 20,
              display: 'flex', alignItems: 'center', gap: 12 }}>
              <span>✅</span> DO
            </div>
            <p style={{ fontSize: 26, lineHeight: 1.6, color: '#bbf7d0', margin: 0,
              display: '-webkit-box', WebkitLineClamp: 7, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
              {doText}
            </p>
          </div>
          <div style={{ flex: 1, background: 'rgba(239,68,68,0.08)', border: '2px solid rgba(239,68,68,0.3)',
            borderRadius: 20, padding: '32px' }}>
            <div style={{ fontSize: 28, fontWeight: 800, color: '#ef4444', marginBottom: 20,
              display: 'flex', alignItems: 'center', gap: 12 }}>
              <span>❌</span> DON'T
            </div>
            <p style={{ fontSize: 26, lineHeight: 1.6, color: '#fca5a5', margin: 0,
              display: '-webkit-box', WebkitLineClamp: 7, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
              {dontText}
            </p>
          </div>
        </div>
      </div>
      <Footer brand={brandName} label="Instagram" />
    </Base>
  );
}

// ─── 5. Checklist Guide ───────────────────────────────────────────────────────
export function ChecklistGuide({ content, brandName, containerRef }: TemplateProps) {
  const lines = content.split('\n').map(l => l.replace(/^[-•*\d.]+\s*/, '').trim()).filter(Boolean);
  const items = lines.length > 1 ? lines : content.split(/[.!?]/).map(s => s.trim()).filter(Boolean);
  const shown = items.slice(0, 6);

  return (
    <Base containerRef={containerRef} bg="linear-gradient(145deg, #0c1f3f 0%, #0d2545 100%)">
      <div style={{ padding: '64px 64px 120px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 44 }}>
          <span style={{ fontSize: 44 }}>📋</span>
          <div style={{ fontSize: 36, fontWeight: 800, color: '#93c5fd' }}>Your Checklist</div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {shown.map((item, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
              <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#3b82f620',
                border: '2px solid #3b82f650', display: 'flex', alignItems: 'center',
                justifyContent: 'center', flexShrink: 0 }}>
                <div style={{ width: 14, height: 14, borderRadius: '50%', background: '#3b82f6' }} />
              </div>
              <p style={{ fontSize: 26, lineHeight: 1.45, color: TEXT, margin: 0,
                display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                {item}
              </p>
            </div>
          ))}
        </div>
      </div>
      <Footer brand={brandName} label="Instagram" />
    </Base>
  );
}

// ─── 6. Nutrition Tips ────────────────────────────────────────────────────────
export function NutritionTips({ content, brandName, containerRef }: TemplateProps) {
  return (
    <Base containerRef={containerRef} bg="linear-gradient(145deg, #1a2e1a 0%, #1f3b1a 100%)">
      <div style={{ position: 'absolute', top: -40, right: -40, width: 200, height: 200,
        borderRadius: '50%', background: 'rgba(132,204,22,0.12)' }} />
      <div style={{ padding: '64px 64px 120px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 44 }}>
          <span style={{ fontSize: 52 }}>🥗</span>
          <div>
            <div style={{ fontSize: 36, fontWeight: 800, color: '#a3e635' }}>Nutrition Tips</div>
            <div style={{ fontSize: 20, color: MUTED, marginTop: 4 }}>Eat well, live well</div>
          </div>
        </div>
        <div style={{ background: 'rgba(132,204,22,0.08)', border: '1px solid rgba(132,204,22,0.2)',
          borderRadius: 20, padding: '36px 40px' }}>
          <p style={{ fontSize: 30, lineHeight: 1.65, color: TEXT, margin: 0,
            display: '-webkit-box', WebkitLineClamp: 9, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
            {content}
          </p>
        </div>
      </div>
      <Footer brand={brandName} label="Instagram" />
    </Base>
  );
}

// ─── 7. Wellness Routine ──────────────────────────────────────────────────────
export function WellnessRoutine({ content, brandName, containerRef }: TemplateProps) {
  const lines = content.split('\n').map(l => l.replace(/^[-•*\d.]+\s*/, '').trim()).filter(Boolean);
  const items = lines.length > 1 ? lines : content.split(/[.!?]/).map(s => s.trim()).filter(Boolean);
  const shown = items.slice(0, 5);
  const icons = ['🌅', '🏃', '🥤', '🧘', '🌙'];

  return (
    <Base containerRef={containerRef} bg="linear-gradient(145deg, #1e1b4b 0%, #312e81 100%)">
      <div style={{ padding: '64px 64px 120px' }}>
        <div style={{ fontSize: 36, fontWeight: 800, color: '#a5b4fc', marginBottom: 44 }}>
          ✨ Daily Wellness Routine
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {shown.map((item, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
              <div style={{ width: 52, height: 52, borderRadius: 14, background: 'rgba(165,180,252,0.15)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 28, flexShrink: 0 }}>
                {icons[i] ?? '⭐'}
              </div>
              <p style={{ fontSize: 26, lineHeight: 1.45, color: TEXT, margin: 0,
                display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                {item}
              </p>
            </div>
          ))}
        </div>
      </div>
      <Footer brand={brandName} label="Instagram" />
    </Base>
  );
}

// ─── 8. Prevention Tips ───────────────────────────────────────────────────────
export function PreventionTips({ content, brandName, containerRef }: TemplateProps) {
  return (
    <Base containerRef={containerRef} bg="linear-gradient(145deg, #1a0a0a 0%, #2d0f0f 100%)">
      <div style={{ position: 'absolute', inset: 0,
        backgroundImage: 'radial-gradient(circle at 20% 80%, rgba(239,68,68,0.12) 0%, transparent 50%)' }} />
      <div style={{ padding: '64px 64px 120px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 44 }}>
          <span style={{ fontSize: 52 }}>🛡️</span>
          <div>
            <div style={{ fontSize: 36, fontWeight: 800, color: '#fca5a5' }}>Prevention Tips</div>
            <div style={{ fontSize: 20, color: MUTED, marginTop: 4 }}>Stay ahead of illness</div>
          </div>
        </div>
        <div style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)',
          borderRadius: 20, padding: '36px 40px' }}>
          <p style={{ fontSize: 30, lineHeight: 1.65, color: TEXT, margin: 0,
            display: '-webkit-box', WebkitLineClamp: 9, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
            {content}
          </p>
        </div>
      </div>
      <Footer brand={brandName} label="Instagram" />
    </Base>
  );
}
