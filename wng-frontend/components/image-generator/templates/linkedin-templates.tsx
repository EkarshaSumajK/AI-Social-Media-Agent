import type { TemplateProps } from '../types';

const W = 1200;
const H = 628;
const FONT = '"Inter", system-ui, -apple-system, sans-serif';
const BG = '#0a0e1a';
const LI_BLUE = '#0a66c2';
const TEXT = '#f0f0f0';
const MUTED = '#8b9ab0';

function Base({ containerRef, children, accent = LI_BLUE }: {
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
      {/* left accent border */}
      <div style={{ position: 'absolute', top: 0, left: 0, width: 6, height: '100%', background: accent }} />
      {/* background grid */}
      <div style={{ position: 'absolute', inset: 0,
        backgroundImage: 'linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)',
        backgroundSize: '60px 60px' }} />
      {children}
    </div>
  );
}

function Footer({ brand, accent = LI_BLUE }: { brand?: string; accent?: string }) {
  return (
    <div style={{ position: 'absolute', bottom: 36, left: 72, right: 72,
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 20 }}>
      <span style={{ color: MUTED, fontSize: 20 }}>{brand ?? 'YourBrand'}</span>
      <span style={{ color: accent, fontWeight: 800, fontSize: 20, letterSpacing: 1 }}>LinkedIn</span>
    </div>
  );
}

// ─── 1. Insight Card ──────────────────────────────────────────────────────────
export function InsightCard({ content, brandName, containerRef }: TemplateProps) {
  return (
    <Base containerRef={containerRef}>
      <div style={{ padding: '52px 72px 100px 84px' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10,
          background: `${LI_BLUE}20`, border: `1px solid ${LI_BLUE}40`,
          borderRadius: 8, padding: '6px 18px', marginBottom: 30 }}>
          <span style={{ color: LI_BLUE, fontSize: 16, fontWeight: 700, letterSpacing: 2, textTransform: 'uppercase' }}>💡 Key Insight</span>
        </div>
        <p style={{ fontSize: 30, lineHeight: 1.65, color: TEXT, maxWidth: 960,
          display: '-webkit-box', WebkitLineClamp: 8, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {content}
        </p>
      </div>
      <Footer brand={brandName} />
    </Base>
  );
}

// ─── 2. Statistic Card ────────────────────────────────────────────────────────
export function StatisticCard({ content, brandName, containerRef }: TemplateProps) {
  const statMatch = content.match(/\d[\d,.%+xX\s]*/);
  const stat = statMatch ? statMatch[0].trim() : '';
  const rest = stat ? content.replace(statMatch![0], '').trim() : content;

  return (
    <Base containerRef={containerRef} accent="#22c55e">
      <div style={{ padding: '44px 72px 100px 84px', display: 'flex', flexDirection: 'column',
        alignItems: 'center', textAlign: 'center' }}>
        <div style={{ fontSize: 16, fontWeight: 800, letterSpacing: 3, textTransform: 'uppercase',
          color: MUTED, marginBottom: 20 }}>Healthcare Statistic</div>
        {stat && (
          <div style={{ fontSize: 100, fontWeight: 900, color: '#22c55e', lineHeight: 1,
            marginBottom: 24, textShadow: '0 0 40px rgba(34,197,94,0.3)' }}>
            {stat}
          </div>
        )}
        <p style={{ fontSize: stat ? 28 : 34, lineHeight: 1.55, color: TEXT, maxWidth: 800,
          display: '-webkit-box', WebkitLineClamp: stat ? 3 : 8, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {rest}
        </p>
      </div>
      <Footer brand={brandName} accent="#22c55e" />
    </Base>
  );
}

// ─── 3. Expert Quote ──────────────────────────────────────────────────────────
export function ExpertQuote({ content, brandName, containerRef }: TemplateProps) {
  return (
    <Base containerRef={containerRef} accent="#8b5cf6">
      <div style={{ padding: '44px 84px 100px' }}>
        <div style={{ fontSize: 120, color: '#8b5cf6', lineHeight: 0.6, marginBottom: 24, fontFamily: 'Georgia, serif' }}>"</div>
        <p style={{ fontSize: 32, lineHeight: 1.65, color: TEXT, maxWidth: 960, fontStyle: 'italic',
          display: '-webkit-box', WebkitLineClamp: 7, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {content}
        </p>
        <div style={{ marginTop: 28, display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 3, background: '#8b5cf6', borderRadius: 2 }} />
          <span style={{ color: '#8b5cf6', fontSize: 18, fontWeight: 600 }}>{brandName ?? 'Healthcare Expert'}</span>
        </div>
      </div>
      <Footer brand={brandName} accent="#8b5cf6" />
    </Base>
  );
}

// ─── 4. Industry Trend ────────────────────────────────────────────────────────
export function IndustryTrend({ content, brandName, containerRef }: TemplateProps) {
  return (
    <Base containerRef={containerRef} accent="#06b6d4">
      <div style={{ padding: '44px 72px 100px 84px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 30 }}>
          <span style={{ fontSize: 32 }}>📈</span>
          <div>
            <div style={{ color: '#06b6d4', fontSize: 18, fontWeight: 800, letterSpacing: 2, textTransform: 'uppercase' }}>Industry Trend</div>
            <div style={{ color: MUTED, fontSize: 15, marginTop: 4 }}>Healthcare Insights 2024</div>
          </div>
        </div>
        <div style={{ borderLeft: '3px solid #06b6d4', paddingLeft: 32, marginBottom: 20 }}>
          <p style={{ fontSize: 30, lineHeight: 1.65, color: TEXT, margin: 0,
            display: '-webkit-box', WebkitLineClamp: 7, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
            {content}
          </p>
        </div>
      </div>
      <Footer brand={brandName} accent="#06b6d4" />
    </Base>
  );
}

// ─── 5. Research Finding ──────────────────────────────────────────────────────
export function ResearchFinding({ content, brandName, containerRef }: TemplateProps) {
  return (
    <Base containerRef={containerRef} accent="#f59e0b">
      <div style={{ padding: '44px 72px 100px 84px' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10,
          background: '#f59e0b15', border: '1px solid #f59e0b30',
          borderRadius: 8, padding: '6px 18px', marginBottom: 30 }}>
          <span style={{ fontSize: 18 }}>🔬</span>
          <span style={{ color: '#f59e0b', fontSize: 16, fontWeight: 700, letterSpacing: 2, textTransform: 'uppercase' }}>Research Finding</span>
        </div>
        <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: 14, padding: '28px 36px' }}>
          <p style={{ fontSize: 30, lineHeight: 1.65, color: TEXT, margin: 0,
            display: '-webkit-box', WebkitLineClamp: 7, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
            {content}
          </p>
        </div>
      </div>
      <Footer brand={brandName} accent="#f59e0b" />
    </Base>
  );
}

// ─── 6. Innovation Highlight ──────────────────────────────────────────────────
export function InnovationHighlight({ content, brandName, containerRef }: TemplateProps) {
  return (
    <Base containerRef={containerRef} accent="#ec4899">
      <div style={{ padding: '44px 72px 100px 84px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 30 }}>
          <div style={{ background: 'linear-gradient(135deg, #ec4899, #8b5cf6)',
            borderRadius: 14, padding: '10px 14px', fontSize: 28 }}>🚀</div>
          <div>
            <div style={{ color: '#ec4899', fontSize: 18, fontWeight: 800, letterSpacing: 2, textTransform: 'uppercase' }}>Healthcare Innovation</div>
            <div style={{ color: MUTED, fontSize: 15, marginTop: 4 }}>What's changing the game</div>
          </div>
        </div>
        <p style={{ fontSize: 30, lineHeight: 1.65, color: TEXT, maxWidth: 960,
          display: '-webkit-box', WebkitLineClamp: 7, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {content}
        </p>
      </div>
      <Footer brand={brandName} accent="#ec4899" />
    </Base>
  );
}

// ─── 7. Case Study Snapshot ───────────────────────────────────────────────────
export function CaseStudySnapshot({ content, brandName, containerRef }: TemplateProps) {
  return (
    <Base containerRef={containerRef} accent={LI_BLUE}>
      <div style={{ padding: '44px 72px 100px 84px' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10,
          background: `${LI_BLUE}15`, border: `1px solid ${LI_BLUE}30`,
          borderRadius: 8, padding: '6px 18px', marginBottom: 30 }}>
          <span style={{ fontSize: 18 }}>📋</span>
          <span style={{ color: LI_BLUE, fontSize: 16, fontWeight: 700, letterSpacing: 2, textTransform: 'uppercase' }}>Case Study</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: MUTED, letterSpacing: 2,
            textTransform: 'uppercase', marginBottom: 12 }}>Overview</div>
          <p style={{ fontSize: 30, lineHeight: 1.65, color: TEXT,
            display: '-webkit-box', WebkitLineClamp: 7, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
            {content}
          </p>
        </div>
      </div>
      <Footer brand={brandName} />
    </Base>
  );
}
