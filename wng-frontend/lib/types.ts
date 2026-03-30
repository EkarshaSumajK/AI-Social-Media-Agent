// ─── Auth / User ─────────────────────────────────────────────────────────────

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  platform: string;
  is_active: boolean;
  created_at: string;
}

// ─── Topics ──────────────────────────────────────────────────────────────────

export interface Topic {
  id: number;
  title: string;
  source_url: string;
  source_name?: string;
  summary?: string;
  relevance_label: string;
  relevance_score: number;
  age_group: string;
  topic_type: string;
  mental_health_specific: boolean;
  screening_reason?: string;
  trust_score: number;
  is_trending: boolean;
  x_engagement_score?: number;
  x_tweet_count?: number;
  x_trend_phrase?: string;
  trend_regions?: string[];
  public_concerns?: string[];
  trend_statements?: string[];
  trend_sentiment?: string;
  statistics?: string[];
  status: string;
  platform: string;
  topic_category?: string;
  region: string;
  created_at: string;
}

export interface DraftTaskStatusResponse {
  task_id: string;
  state: string;
  status: string;
  message: string;
  article_id?: number;
  progress?: number;
  stage?: string;
}

export interface CollectTopicsResponse {
  fetched: number;
  x_topics_found: number;
  x_preferred_country: string;
  x_india_tweets: number;
  x_us_tweets: number;
  article_heading_queries: string[];
  articles_per_heading_target: number;
  stored: number;
  skipped: number;
  duplicate_rejected: number;
  screened_out: number;
  trust_rejected: number;
  replaced_existing: number;
  trending_tweets: unknown[];
}

export interface GenerateDraftResponse {
  status: string;
  message: string;
  article_id?: number;
  task_id?: string;
}

export interface SocialPublishResponse {
  article_id: number;
  outcomes: Record<string, string>;
}

export interface MessageResponse {
  message: string;
}

export const TOPIC_CATEGORIES = [
  'anxiety',
  'depression',
  'adhd',
  'autism',
  'trauma',
  'stress',
  'parenting',
  'relationships',
  'workplace',
  'general',
] as const;

export const REGIONS = ['global', 'india', 'us', 'uk', 'australia'] as const;

// ─── Articles / Drafts ───────────────────────────────────────────────────────

export interface SocialPost {
  id: number;
  platform: string;
  caption: string;
  edited_caption?: string;
  status: string;
  external_post_id?: string;
  error_message?: string;
  image_url?: string;
  posted_at?: string;
}

export interface Article {
  id: number;
  topic_id: number;
  status: string;
  seo_title: string;
  meta_description: string;
  keywords?: string[];
  content_html: string;
  issue_summary: string;
  why_it_matters: string;
  mental_health_implications: string;
  professional_insight: string;
  how_services_help: string;
  call_to_action: string;
  disclaimer_text: string;
  readability_score?: number;
  ai_generated_probability?: number;
  source_similarity_score?: number;
  structure_valid: boolean;
  quality_notes?: string[];
  source_url: string;
  body_image_url?: string;
  field_image_urls?: Record<string, string>;
  platform: string;
  slug?: string;
  virality_score?: number;
  clarity_score?: number;
  hook_strength_score?: number;
  conversion_score?: number;
  requires_review?: boolean;
  created_by?: number;
  approved_by?: number;
  approved_at?: string;
  published_at?: string;
  published_url?: string;
  created_at: string;
  updated_at: string;
  topic?: Topic;
  social_posts: SocialPost[];
}

export interface PublishedArticle {
  id: number;
  slug?: string;
  seo_title: string;
  meta_description: string;
  keywords?: string[];
  content_html: string;
  platform: string;
  published_at?: string;
  published_url?: string;
}

// ─── Audit ───────────────────────────────────────────────────────────────────

export interface AuditLog {
  id: number;
  actor_id?: number;
  action: string;
  entity_type: string;
  entity_id: string;
  details?: Record<string, unknown>;
  created_at: string;
}

// ─── Performance ─────────────────────────────────────────────────────────────

export interface PerformanceMetric {
  metric: string;
  value: number | string;
  change_pct?: number;
}

export interface PerformanceMetrics {
  platform?: string;
  days: number;
  metrics: PerformanceMetric[];
}

export interface PerformanceInsight {
  insights: string;
  recommendations: string[];
}

// ─── Scheduling ──────────────────────────────────────────────────────────────

export interface ScheduledPost {
  id: number;
  title: string;
  content: string;
  platform: string;
  content_type: string;
  scheduled_for?: string;
  status: string;
  hashtags?: string[];
  media_urls?: string[];
  campaign_id?: number;
  social_account_id?: number;
  published_at?: string;
  error_message?: string;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface ScheduledPostCreate {
  title: string;
  content: string;
  platform: string;
  content_type?: string;
  scheduled_for?: string;
  hashtags?: string[];
  media_urls?: string[];
  campaign_id?: number;
}

export interface CalendarStats {
  total: number;
  scheduled: number;
  draft: number;
  published: number;
  failed: number;
}

// ─── Thought Leadership ──────────────────────────────────────────────────────

export type ThoughtLeadershipContentType =
  | 'deep_insight'
  | 'predictions'
  | 'contrarian'
  | 'framework'
  | 'case_study'
  | 'authority_thread'
  | 'hard_truths'
  | 'founder_journey'
  | 'myth_busting';

export const LEADERSHIP_TYPES: { value: ThoughtLeadershipContentType; label: string }[] = [
  { value: 'deep_insight', label: 'Deep Insight' },
  { value: 'predictions', label: 'Predictions' },
  { value: 'contrarian', label: 'Contrarian Take' },
  { value: 'framework', label: 'Framework' },
  { value: 'case_study', label: 'Case Study' },
  { value: 'authority_thread', label: 'Authority Thread' },
  { value: 'hard_truths', label: 'Hard Truths' },
  { value: 'founder_journey', label: 'Founder Journey' },
  { value: 'myth_busting', label: 'Myth Busting' },
];

export interface ThoughtLeadershipResponse {
  id: number;
  content_type: string;
  topic: string;
  industry: string;
  content: string;
  created_at: string;
}

// ─── Platform Content ────────────────────────────────────────────────────────

export type PlatformContentTarget = 'linkedin' | 'instagram' | 'twitter' | 'youtube';

export interface PlatformContentResponse {
  id: number;
  topic: string;
  platform: string;
  content_type: string;
  content: string;
  image_url?: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

// ─── YouTube Shorts ──────────────────────────────────────────────────────────

export interface YoutubeShortResponse {
  id: number;
  topic: string;
  target_audience?: string;
  duration: number;
  hook: string;
  script: Record<string, unknown>;
  titles: string[];
  description: string;
  tags: string[];
  created_at: string;
}

// ─── Campaigns ───────────────────────────────────────────────────────────────

export interface CampaignPiece {
  id: number;
  campaign_id: number;
  phase: string;
  content_type: string;
  platform?: string;
  content: string;
  scheduled_for?: string;
  status: string;
}

export interface Campaign {
  id: number;
  title: string;
  event_date?: string;
  goal?: string;
  audience_description?: string;
  platforms?: string[];
  platform_entity: string;
  status: string;
  created_by: number;
  created_at: string;
  pieces: CampaignPiece[];
}

// ─── Competitors ─────────────────────────────────────────────────────────────

export interface Competitor {
  id: number;
  name: string;
  platform: string;
  profile_url: string;
  platform_entity: string;
  created_by: number;
}

export interface CompetitorAnalysis {
  id: number;
  competitor_id: number;
  name: string;
  analysis: string;
  created_at: string;
}

export interface CompetitorAnalysisStored {
  id: number;
  competitor_id: number;
  analysis: string;
  created_at: string;
}

// ─── Hooks ───────────────────────────────────────────────────────────────────

export interface HookTemplate {
  id: number;
  hook_text: string;
  category: string;
  platform: string;
  industry?: string;
  use_count: number;
  created_by?: number;
}

export interface HookSuggestion {
  hook_text: string;
  reasoning?: string;
}

export interface HookSuggestionResponse {
  suggestions: HookSuggestion[];
}

// ─── Swipe Files ─────────────────────────────────────────────────────────────

export interface SwipeFile {
  id: number;
  created_by: number;
  platform: string;
  title: string;
  content: string;
  source_url?: string;
  performance_notes?: string;
  tags?: string[];
  created_at: string;
}

// ─── Repurpose ───────────────────────────────────────────────────────────────

export type RepurposeSourceType = 'article' | 'webinar' | 'blog' | 'linkedin' | 'twitter' | 'instagram' | 'youtube';

export interface RepurposeResponse {
  results: Record<string, string | string[]>;
}

export const REPURPOSE_TARGET_FORMATS = [
  { value: 'linkedin_post', label: 'LinkedIn Post' },
  { value: 'twitter_thread', label: 'Twitter Thread' },
  { value: 'instagram_caption', label: 'Instagram Caption' },
  { value: 'email_newsletter', label: 'Email Newsletter' },
  { value: 'short_video_script', label: 'Short Video Script' },
  { value: 'blog_summary', label: 'Blog Summary' },
] as const;

// ─── Audience Content ────────────────────────────────────────────────────────

export type AudienceAwarenessStage = 'cold' | 'warm' | 'hot';

export interface AudienceContentResponse {
  results: Record<string, string>;
}

export const AUDIENCE_STAGES: { value: AudienceAwarenessStage; label: string }[] = [
  { value: 'cold', label: 'Cold (Unaware)' },
  { value: 'warm', label: 'Warm (Problem Aware)' },
  { value: 'hot', label: 'Hot (Solution Aware)' },
];

// ─── Daily Posts ─────────────────────────────────────────────────────────────

export interface DailyPostSuggestion {
  post_type: string;
  content: string;
  platform_hint?: string;
}

export interface DailyPostBatch {
  id: number;
  industry: string;
  region: string;
  target_audience: string;
  business_goal: string;
  suggestions: DailyPostSuggestion[];
  created_at: string;
}

// ─── Social Accounts ─────────────────────────────────────────────────────────

export interface SocialAccount {
  id: number;
  platform: string;
  account_name: string;
  account_id?: string;
  status: string;
  profile_image_url?: string;
  token_expires_at?: string;
  created_at: string;
}

// ─── Scoring ─────────────────────────────────────────────────────────────────

export interface ContentScoreResponse {
  article_id: number;
  virality_score: number;
  clarity_score: number;
  hook_strength_score: number;
  conversion_score: number;
  breakdown: Record<string, string | string[]>;
}

// ─── Regional ────────────────────────────────────────────────────────────────

export interface LocaliseResponse {
  id: number;
  region: string;
  language_style: string;
  original_content: string;
  localised_content: string;
  created_at: string;
}

export interface RegionalTrendingTopic {
  topic: string;
  relevance_reason: string;
  content_angle: string;
  urgency: string;
}

export interface RegionalTrendingResponse {
  id: number;
  region: string;
  industry: string;
  trending_topics: RegionalTrendingTopic[];
  created_at: string;
}

export interface RegionalHashtagResponse {
  id: number;
  region: string;
  platform: string;
  topic: string;
  hashtags: { primary: string[]; secondary: string[]; trending: string[] };
  created_at: string;
}

export interface RegionalHistoryItem {
  id: number;
  content_type: string;
  region: string;
  created_at: string;
  [key: string]: unknown;
}

// ─── Constants ───────────────────────────────────────────────────────────────

export const PLATFORMS = [
  { value: 'horizon', label: 'Horizon' },
  { value: 'connect', label: 'Connect' },
  { value: 'parentshala', label: 'Parentshala' },
] as const;

export const SOCIAL_PLATFORMS = [
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'twitter', label: 'Twitter / X' },
  { value: 'facebook', label: 'Facebook' },
  { value: 'youtube', label: 'YouTube' },
] as const;
