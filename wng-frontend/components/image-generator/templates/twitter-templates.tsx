import type { TemplateProps } from '../types';

const W = 1200;
const H = 675;
const FONT = '"Inter", system-ui, -apple-system, sans-serif';
const BG = '#0d1117';
const TWITTER_BLUE = '#1d9bf0';
const TEXT = '#e7e9ea';
const MUTED = '#71767b';

function Base({ containerRef, children, accent = TWITTER_BLUE }: {
  containerRef?: React.Ref<HTMLDivElement>;
  children: React.ReactNode;
  accent?: string;
}) {
  return (
    <div
      ref={containerRef}
      style={{ width: W, height: H, background: BG, fontFamily: FONT, color: TEXT,
        position: 'relative', overflow: 'hidden', boxSizing: 'border-box' }}
    >
      {/* top accent bar */}
      <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: 5, background: accent }} />
      {/* decorative circles */}
      <div style={{ position: 'absolute', bottom: -80, right: -80, width: 280, height: 280,
        borderRadius: '50%', background: `${accent}10` }} />
      <div style={{ position: 'absolute', top: 60, left: -60, width: 180, height: 180,
        borderRadius: '50%', background: `${accent}08` }} />
      {children}
    </div>
  );
}

function Footer({ brand, accent = TWITTER_BLUE }: { brand?: string; accent?: string }) {
  return (
    <div style={{ position: 'absolute', bottom: 40, left: 72, right: 72,
      display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <span style={{ color: MUTED, fontSize: 22 }}>{brand ?? '@YourBrand'}</span>
      <span style={{ color: accent, fontSize: 22, fontWeight: 700 }}>𝕏</span>
    </div>
  );
}

// ─── 1. Tip Card ──────────────────────────────────────────────────────────────
export function TipCard({ content, brandName, containerRef }: TemplateProps) {
  return (
    <Base containerRef={containerRef}>
      <div style={{ padding: '64px 72px 100px' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10,
          background: `${TWITTER_BLUE}20`, border: `1px solid ${TWITTER_BLUE}40`,
          borderRadius: 30, padding: '8px 20px', marginBottom: 36 }}>
          <span style={{ fontSize: 22 }}>💡</span>
          <span style={{ color: TWITTER_BLUE, fontSize: 18, fontWeight: 700, letterSpacing: 2, textTransform: 'uppercase' }}>Health Tip</span>
        </div>
        <p style={{ fontSize: 34, lineHeight: 1.55, color: TEXT, maxWidth: 900,
          display: '-webkit-box', WebkitLineClamp: 8, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {content}
        </p>
      </div>
      <Footer brand={brandName} />
    </Base>
  );
}

// ─── 2. Myth vs Fact ──────────────────────────────────────────────────────────
export function MythVsFact({ content, brandName, containerRef }: TemplateProps) {
  const mythMatch = content.match(/myth[:\s]+(.+?)(?=fact[:\s]|$)/is);
  const factMatch = content.match(/fact[:\s]+(.+)/is);
  const half = Math.floor(content.length / 2);
  const myth = mythMatch ? mythMatch[1].trim() : content.slice(0, half).trim();
  const fact = factMatch ? factMatch[1].trim() : content.slice(half).trim();

  return (
    <Base containerRef={containerRef} accent="#ef4444">
      <div style={{ padding: '54px 72px 100px' }}>
        <div style={{ fontSize: 18, fontWeight: 800, letterSpacing: 3, textTransform: 'uppercase',
          color: MUTED, marginBottom: 32 }}>Myth vs Fact</div>
        <div style={{ display: 'flex', gap: 32 }}>
          <div style={{ flex: 1, background: '#ef444415', border: '1px solid #ef444430',
            borderRadius: 16, padding: '32px 36px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
              <span style={{ fontSize: 24 }}>❌</span>
              <span style={{ color: '#ef4444', fontWeight: 800, fontSize: 18, letterSpacing: 2, textTransform: 'uppercase' }}>Myth</span>
            </div>
            <p style={{ fontSize: 26, lineHeight: 1.5, color: '#fca5a5', display: '-webkit-box',
              WebkitLineClamp: 5, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{myth}</p>
          </div>
          <div style={{ flex: 1, background: '#22c55e15', border: '1px solid #22c55e30',
            borderRadius: 16, padding: '32px 36px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
              <span style={{ fontSize: 24 }}>✅</span>
              <span style={{ color: '#22c55e', fontWeight: 800, fontSize: 18, letterSpacing: 2, textTransform: 'uppercase' }}>Fact</span>
            </div>
            <p style={{ fontSize: 26, lineHeight: 1.5, color: '#86efac', display: '-webkit-box',
              WebkitLineClamp: 5, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{fact}</p>
          </div>
        </div>
      </div>
      <Footer brand={brandName} accent="#ef4444" />
    </Base>
  );
}

// ─── 3. Health Reminder ───────────────────────────────────────────────────────
export function HealthReminder({ content, brandName, containerRef }: TemplateProps) {
  return (
    <Base containerRef={containerRef} accent="#f59e0b">
      <div style={{ padding: '64px 72px 100px' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10,
          background: '#f59e0b20', border: '1px solid #f59e0b40',
          borderRadius: 30, padding: '8px 20px', marginBottom: 36 }}>
          <span style={{ fontSize: 22 }}>🔔</span>
          <span style={{ color: '#f59e0b', fontSize: 18, fontWeight: 700, letterSpacing: 2, textTransform: 'uppercase' }}>Health Reminder</span>
        </div>
        <p style={{ fontSize: 36, lineHeight: 1.6, color: TEXT, maxWidth: 900,
          display: '-webkit-box', WebkitLineClamp: 7, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {content}
        </p>
      </div>
      <Footer brand={brandName} accent="#f59e0b" />
    </Base>
  );
}

// ─── 4. Quick Statistic ───────────────────────────────────────────────────────
export function QuickStatistic({ content, brandName, containerRef }: TemplateProps) {
  const statMatch = content.match(/\d[\d,.%+xX\s]*/);
  const stat = statMatch ? statMatch[0].trim() : '';
  const rest = stat ? content.replace(statMatch![0], '').trim() : content;

  return (
    <Base containerRef={containerRef} accent={TWITTER_BLUE}>
      <div style={{ padding: '60px 72px 100px', display: 'flex', flexDirection: 'column',
        alignItems: 'center', textAlign: 'center' }}>
        <div style={{ fontSize: 18, fontWeight: 800, letterSpacing: 3, textTransform: 'uppercase',
          color: MUTED, marginBottom: 24 }}>Quick Statistic</div>
        {stat && (
          <div style={{ fontSize: 110, fontWeight: 900, color: TWITTER_BLUE, lineHeight: 1,
            marginBottom: 28, textShadow: `0 0 60px ${TWITTER_BLUE}40` }}>
            {stat}
          </div>
        )}
        <p style={{ fontSize: stat ? 30 : 38, lineHeight: 1.5, color: TEXT, maxWidth: 800,
          display: '-webkit-box', WebkitLineClamp: stat ? 4 : 8, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {rest}
        </p>
      </div>
      <Footer brand={brandName} />
    </Base>
  );
}

// ─── 5. Checklist Tip ─────────────────────────────────────────────────────────
export function ChecklistTip({ content, brandName, containerRef }: TemplateProps) {
  const lines = content.split('\n').map(l => l.replace(/^[-•*\d.]+\s*/, '').trim()).filter(Boolean);
  const items = lines.length > 1 ? lines : content.split(/[.!?]/).map(s => s.trim()).filter(Boolean);
  const shown = items.slice(0, 5);

  return (
    <Base containerRef={containerRef} accent="#22c55e">
      <div style={{ padding: '54px 72px 100px' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10,
          background: '#22c55e20', border: '1px solid #22c55e40',
          borderRadius: 30, padding: '8px 20px', marginBottom: 36 }}>
          <span style={{ fontSize: 22 }}>✅</span>
          <span style={{ color: '#22c55e', fontSize: 18, fontWeight: 700, letterSpacing: 2, textTransform: 'uppercase' }}>Checklist</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {shown.map((item, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 18 }}>
              <div style={{ width: 32, height: 32, borderRadius: 8, background: '#22c55e20',
                border: '1px solid #22c55e50', display: 'flex', alignItems: 'center',
                justifyContent: 'center', flexShrink: 0, marginTop: 2 }}>
                <span style={{ color: '#22c55e', fontWeight: 800, fontSize: 14 }}>{i + 1}</span>
              </div>
              <p style={{ fontSize: 28, lineHeight: 1.5, color: TEXT, margin: 0,
                display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                {item}
              </p>
            </div>
          ))}
        </div>
      </div>
      <Footer brand={brandName} accent="#22c55e" />
    </Base>
  );
}

// ─── 6. Awareness Message ─────────────────────────────────────────────────────
export function AwarenessMessage({ content, brandName, containerRef }: TemplateProps) {
  return (
    <Base containerRef={containerRef} accent="#8b5cf6">
      <div style={{ padding: '64px 72px 100px', display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', height: '100%', textAlign: 'center' }}>
        <span style={{ fontSize: 60, marginBottom: 32 }}>🏥</span>
        <p style={{ fontSize: 38, lineHeight: 1.55, color: TEXT, maxWidth: 880, fontWeight: 500,
          display: '-webkit-box', WebkitLineClamp: 6, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {content}
        </p>
      </div>
      <Footer brand={brandName} accent="#8b5cf6" />
    </Base>
  );
}

// ─── 7. Daily Health Habit ────────────────────────────────────────────────────
export function DailyHealthHabit({ content, brandName, containerRef }: TemplateProps) {
  return (
    <Base containerRef={containerRef} accent="#06b6d4">
      <div style={{ padding: '54px 72px 100px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 36 }}>
          <div style={{ width: 56, height: 56, borderRadius: 14, background: '#06b6d420',
            border: '1px solid #06b6d440', display: 'flex', alignItems: 'center',
            justifyContent: 'center', fontSize: 28 }}>🌿</div>
          <div>
            <div style={{ color: '#06b6d4', fontSize: 18, fontWeight: 800, letterSpacing: 2, textTransform: 'uppercase' }}>Daily Health Habit</div>
            <div style={{ color: MUTED, fontSize: 16, marginTop: 4 }}>Build better routines</div>
          </div>
        </div>
        <div style={{ background: '#ffffff08', border: '1px solid #ffffff12', borderRadius: 20, padding: '36px 44px' }}>
          <p style={{ fontSize: 34, lineHeight: 1.6, color: TEXT, margin: 0,
            display: '-webkit-box', WebkitLineClamp: 7, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
            {content}
          </p>
        </div>
      </div>
      <Footer brand={brandName} accent="#06b6d4" />
    </Base>
  );
}
