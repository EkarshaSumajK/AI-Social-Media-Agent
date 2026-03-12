import type { TemplateRegistry } from './types';
import {
  TipCard, MythVsFact, HealthReminder as TwitterHealthReminder,
  QuickStatistic, ChecklistTip, AwarenessMessage, DailyHealthHabit,
} from './templates/twitter-templates';
import {
  InsightCard, StatisticCard, ExpertQuote, IndustryTrend,
  ResearchFinding, InnovationHighlight, CaseStudySnapshot,
} from './templates/linkedin-templates';
import {
  CarouselCover, HealthTips, SymptomsExplainer, DoVsDont,
  ChecklistGuide, NutritionTips, WellnessRoutine, PreventionTips,
} from './templates/instagram-templates';
import {
  QuoteCard, SimpleTip, HealthReminder as ThreadsHealthReminder,
  QuickFact, ConversationStarter, DailyWellnessTip,
} from './templates/threads-templates';
import {
  NumberList, WarningThumbnail, MythBusting, SymptomsGuide,
  DoctorExplains, BeforeVsAfter, TopMistakes,
} from './templates/youtube-templates';

export const TEMPLATE_REGISTRY: TemplateRegistry = {
  twitter: [
    { id: 'tip-card',           label: 'Tip Card',            width: 1200, height: 675, component: TipCard },
    { id: 'myth-vs-fact',       label: 'Myth vs Fact',        width: 1200, height: 675, component: MythVsFact },
    { id: 'health-reminder',    label: 'Health Reminder',     width: 1200, height: 675, component: TwitterHealthReminder },
    { id: 'quick-statistic',    label: 'Quick Statistic',     width: 1200, height: 675, component: QuickStatistic },
    { id: 'checklist-tip',      label: 'Checklist Tip',       width: 1200, height: 675, component: ChecklistTip },
    { id: 'awareness-message',  label: 'Awareness Message',   width: 1200, height: 675, component: AwarenessMessage },
    { id: 'daily-health-habit', label: 'Daily Health Habit',  width: 1200, height: 675, component: DailyHealthHabit },
  ],
  linkedin: [
    { id: 'insight-card',          label: 'Insight Card',            width: 1200, height: 628, component: InsightCard },
    { id: 'statistic-card',        label: 'Statistic Card',          width: 1200, height: 628, component: StatisticCard },
    { id: 'expert-quote',          label: 'Expert Quote',            width: 1200, height: 628, component: ExpertQuote },
    { id: 'industry-trend',        label: 'Industry Trend',          width: 1200, height: 628, component: IndustryTrend },
    { id: 'research-finding',      label: 'Research Finding',        width: 1200, height: 628, component: ResearchFinding },
    { id: 'innovation-highlight',  label: 'Innovation Highlight',    width: 1200, height: 628, component: InnovationHighlight },
    { id: 'case-study-snapshot',   label: 'Case Study Snapshot',     width: 1200, height: 628, component: CaseStudySnapshot },
  ],
  instagram: [
    { id: 'carousel-cover',     label: 'Carousel Cover',      width: 1080, height: 1080, component: CarouselCover },
    { id: 'health-tips',        label: 'Health Tips',         width: 1080, height: 1080, component: HealthTips },
    { id: 'symptoms-explainer', label: 'Symptoms Explainer',  width: 1080, height: 1080, component: SymptomsExplainer },
    { id: 'do-vs-dont',         label: 'Do vs Don\'t',        width: 1080, height: 1080, component: DoVsDont },
    { id: 'checklist-guide',    label: 'Checklist Guide',     width: 1080, height: 1080, component: ChecklistGuide },
    { id: 'nutrition-tips',     label: 'Nutrition Tips',      width: 1080, height: 1080, component: NutritionTips },
    { id: 'wellness-routine',   label: 'Wellness Routine',    width: 1080, height: 1080, component: WellnessRoutine },
    { id: 'prevention-tips',    label: 'Prevention Tips',     width: 1080, height: 1080, component: PreventionTips },
  ],
  threads: [
    { id: 'quote-card',           label: 'Quote Card',            width: 1080, height: 1080, component: QuoteCard },
    { id: 'simple-tip',           label: 'Simple Tip',            width: 1080, height: 1080, component: SimpleTip },
    { id: 'health-reminder',      label: 'Health Reminder',       width: 1080, height: 1080, component: ThreadsHealthReminder },
    { id: 'quick-fact',           label: 'Quick Fact',            width: 1080, height: 1080, component: QuickFact },
    { id: 'conversation-starter', label: 'Conversation Starter',  width: 1080, height: 1080, component: ConversationStarter },
    { id: 'daily-wellness-tip',   label: 'Daily Wellness Tip',    width: 1080, height: 1080, component: DailyWellnessTip },
  ],
  youtube: [
    { id: 'number-list',       label: 'Number List',        width: 1280, height: 720, component: NumberList },
    { id: 'warning-thumbnail', label: 'Warning Thumbnail',  width: 1280, height: 720, component: WarningThumbnail },
    { id: 'myth-busting',      label: 'Myth Busting',       width: 1280, height: 720, component: MythBusting },
    { id: 'symptoms-guide',    label: 'Symptoms Guide',     width: 1280, height: 720, component: SymptomsGuide },
    { id: 'doctor-explains',   label: 'Doctor Explains',    width: 1280, height: 720, component: DoctorExplains },
    { id: 'before-vs-after',   label: 'Before vs After',    width: 1280, height: 720, component: BeforeVsAfter },
    { id: 'top-mistakes',      label: 'Top Mistakes',       width: 1280, height: 720, component: TopMistakes },
  ],
};

// Map content_type / post_type → default template id per platform
export const CONTENT_TYPE_DEFAULT: Record<string, Record<string, string>> = {
  twitter: {
    authority_post:  'tip-card',
    thread:          'checklist-tip',
    poll_post:       'awareness-message',
    trending_topic:  'quick-statistic',
    storytelling:    'health-reminder',
    authority:       'tip-card',
    engagement:      'awareness-message',
  },
  linkedin: {
    authority_post:   'insight-card',
    thread:           'insight-card',
    poll_post:        'statistic-card',
    trending_topic:   'industry-trend',
    storytelling:     'expert-quote',
    authority:        'insight-card',
    engagement:       'expert-quote',
    reel_script:      'innovation-highlight',
    video_outline:    'case-study-snapshot',
  },
  instagram: {
    authority_post:  'health-tips',
    thread:          'checklist-guide',
    reel_script:     'carousel-cover',
    poll_post:       'do-vs-dont',
    trending_topic:  'symptoms-explainer',
    storytelling:    'wellness-routine',
    short_form_video: 'carousel-cover',
  },
  threads: {
    authority_post:  'simple-tip',
    thread:          'quote-card',
    poll_post:       'conversation-starter',
    trending_topic:  'quick-fact',
    storytelling:    'quote-card',
    engagement:      'conversation-starter',
  },
  youtube: {
    authority_post:  'number-list',
    thread:          'number-list',
    reel_script:     'doctor-explains',
    video_outline:   'number-list',
    poll_post:       'myth-busting',
    trending_topic:  'warning-thumbnail',
    short_form_video: 'top-mistakes',
  },
};
