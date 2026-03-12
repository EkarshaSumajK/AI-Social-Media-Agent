import type { TemplateProps } from '../types';

const W = 1080;
const H = 1080;
const FONT = '"Inter", system-ui, -apple-system, sans-serif';
const BG = '#101010';
const TEXT = '#f0f0f0';
const MUTED = '#6b7280';

function Base({ containerRef, children, accent = '#ffffff' }: {
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
      <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 3, background: accent }} />
      {children}
    </div>
  );
}

function Footer({ brand }: { brand?: string }) {
  return (
    <div style={{ position: 'absolute', bottom: 24, left: 64, right: 64,
      display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <span style={{ color: MUTED, fontSize: 22 }}>{brand ?? '@YourBrand'}</span>
      <span style={{ color: MUTED, fontSize: 22 }}>Threads</span>
    </div>
  );
}

// ─── 1. Quote Card ────────────────────────────────────────────────────────────
export function QuoteCard({ content, brandName, containerRef }: TemplateProps) {
  return (
    <Base containerRef={containerRef}>
      <div style={{ padding: '80px 64px 100px', display: 'flex', flexDirection: 'column',
        justifyContent: 'center', height: '100%' }}>
        <div style={{ fontSize: 160, color: 'rgba(255,255,255,0.06)', lineHeight: 0.5,
          fontFamily: 'Georgia, serif', marginBottom: 20 }}>"</div>
        <p style={{ fontSize: 42, lineHeight: 1.55, color: TEXT, maxWidth: 900, fontWeight: 400,
          display: '-webkit-box', WebkitLineClamp: 7, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {content}
        </p>
      </div>
      <Footer brand={brandName} />
    </Base>
  );
}

// ─── 2. Simple Tip ────────────────────────────────────────────────────────────
export function SimpleTip({ content, brandName, containerRef }: TemplateProps) {
  return (
    <Base containerRef={containerRef} accent="#22c55e">
      <div style={{ padding: '80px 64px 100px', display: 'flex', flexDirection: 'column',
        justifyContent: 'center', height: '100%' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 12, marginBottom: 44,
          background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.25)',
          borderRadius: 30, padding: '10px 24px', width: 'fit-content' }}>
          <span style={{ fontSize: 24 }}>💡</span>
          <span style={{ color: '#22c55e', fontSize: 20, fontWeight: 700, letterSpacing: 2, textTransform: 'uppercase' }}>Health Tip</span>
        </div>
        <p style={{ fontSize: 40, lineHeight: 1.6, color: TEXT,
          display: '-webkit-box', WebkitLineClamp: 8, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {content}
        </p>
      </div>
      <Footer brand={brandName} />
    </Base>
  );
}

// ─── 3. Health Reminder ───────────────────────────────────────────────────────
export function HealthReminder({ content, brandName, containerRef }: TemplateProps) {
  return (
    <Base containerRef={containerRef} accent="#f59e0b">
      <div style={{ padding: '80px 64px 100px', display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', textAlign: 'center', height: '100%' }}>
        <span style={{ fontSize: 72, marginBottom: 36 }}>🔔</span>
        <div style={{ fontSize: 18, fontWeight: 800, color: '#f59e0b', letterSpacing: 3,
          textTransform: 'uppercase', marginBottom: 28 }}>Reminder</div>
        <p style={{ fontSize: 40, lineHeight: 1.6, color: TEXT, maxWidth: 880,
          display: '-webkit-box', WebkitLineClamp: 7, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {content}
        </p>
      </div>
      <Footer brand={brandName} />
    </Base>
  );
}

// ─── 4. Quick Fact ────────────────────────────────────────────────────────────
export function QuickFact({ content, brandName, containerRef }: TemplateProps) {
  return (
    <Base containerRef={containerRef} accent="#3b82f6">
      <div style={{ padding: '80px 64px 100px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 48 }}>
          <div style={{ width: 52, height: 52, borderRadius: '50%', background: '#3b82f620',
            border: '1px solid #3b82f640', display: 'flex', alignItems: 'center',
            justifyContent: 'center', fontSize: 26 }}>📌</div>
          <span style={{ color: '#3b82f6', fontSize: 20, fontWeight: 800, letterSpacing: 2, textTransform: 'uppercase' }}>Quick Fact</span>
        </div>
        <div style={{ borderLeft: '4px solid #3b82f6', paddingLeft: 40 }}>
          <p style={{ fontSize: 40, lineHeight: 1.6, color: TEXT, margin: 0,
            display: '-webkit-box', WebkitLineClamp: 8, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
            {content}
          </p>
        </div>
      </div>
      <Footer brand={brandName} />
    </Base>
  );
}

// ─── 5. Conversation Starter ──────────────────────────────────────────────────
export function ConversationStarter({ content, brandName, containerRef }: TemplateProps) {
  const question = content.includes('?') ? content : `${content}?`;
  return (
    <Base containerRef={containerRef} accent="#8b5cf6">
      <div style={{ padding: '80px 64px 100px', display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', textAlign: 'center', height: '100%' }}>
        <div style={{ fontSize: 18, fontWeight: 800, color: '#8b5cf6', letterSpacing: 3,
          textTransform: 'uppercase', marginBottom: 36 }}>💬 Let's Talk</div>
        <p style={{ fontSize: 44, lineHeight: 1.5, color: TEXT, maxWidth: 880, fontWeight: 600,
          display: '-webkit-box', WebkitLineClamp: 7, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {question}
        </p>
        <div style={{ marginTop: 44, fontSize: 22, color: MUTED }}>Share your thoughts below 👇</div>
      </div>
      <Footer brand={brandName} />
    </Base>
  );
}

// ─── 6. Daily Wellness Tip ────────────────────────────────────────────────────
export function DailyWellnessTip({ content, brandName, containerRef }: TemplateProps) {
  return (
    <Base containerRef={containerRef} accent="#06b6d4">
      <div style={{ padding: '80px 64px 100px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 52 }}>
          <span style={{ fontSize: 52 }}>🌿</span>
          <div>
            <div style={{ fontSize: 30, fontWeight: 800, color: '#67e8f9' }}>Daily Wellness</div>
            <div style={{ fontSize: 20, color: MUTED, marginTop: 4 }}>Small habits, big results</div>
          </div>
        </div>
        <p style={{ fontSize: 40, lineHeight: 1.65, color: TEXT,
          display: '-webkit-box', WebkitLineClamp: 8, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {content}
        </p>
      </div>
      <Footer brand={brandName} />
    </Base>
  );
}
