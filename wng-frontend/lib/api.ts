import { getStoredToken } from './auth';
import type {
  Article,
  AudienceContentResponse,
  CalendarStats,
  Campaign,
  CollectTopicsResponse,
  CompetitorAnalysis,
  CompetitorAnalysisStored,
  Competitor,
  ContentScoreResponse,
  DailyPostBatch,
  DraftTaskStatusResponse,
  GenerateDraftResponse,
  HookSuggestionResponse,
  HookTemplate,
  LocaliseResponse,
  MessageResponse,
  PerformanceInsight,
  PerformanceMetrics,
  PlatformContentResponse,
  PublishedArticle,
  RegionalHashtagResponse,
  RegionalHistoryItem,
  RegionalTrendingResponse,
  RepurposeResponse,
  ScheduledPost,
  ScheduledPostCreate,
  SocialAccount,
  SocialPublishResponse,
  SwipeFile,
  ThoughtLeadershipResponse,
  Topic,
  User,
  YoutubeShortResponse,
} from './types';

// ---------------------------------------------------------------------------
// Base
// ---------------------------------------------------------------------------

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1';

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getStoredToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init.headers as Record<string, string>),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...init, headers });

  if (!res.ok) {
    let message = `Request failed: ${res.status}`;
    try {
      const body = await res.json();
      message = body?.detail ?? message;
    } catch {
      // ignore
    }
    throw new Error(message);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export async function login(email: string, password: string): Promise<{ access_token: string; user: User }> {
  return request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function fetchMe(): Promise<User> {
  return request('/auth/me');
}

// ---------------------------------------------------------------------------
// Topics
// ---------------------------------------------------------------------------

export interface FetchTopicsParams {
  since?: string;
  q?: string;
  topic_category?: string;
  region?: string;
  is_trending?: boolean | string;
  trust_min?: string;
  status?: string;
  limit?: string;
  offset?: string;
}

export async function fetchTopics(params?: FetchTopicsParams): Promise<Topic[]> {
  const clean: Record<string, string> = {};
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== '') {
        clean[k] = String(v);
      }
    }
  }
  const qs = new URLSearchParams(clean).toString();
  return request(`/topics${qs ? `?${qs}` : ''}`);
}

export async function collectTopics(query?: string): Promise<CollectTopicsResponse> {
  return request('/topics/collect', {
    method: 'POST',
    body: JSON.stringify({ query }),
  });
}

export async function generateDraft(topicId: number, runAsync = true): Promise<GenerateDraftResponse> {
  return request(`/topics/${topicId}/generate-draft`, {
    method: 'POST',
    body: JSON.stringify({ run_async: runAsync }),
  });
}

export async function fetchDraftTaskStatus(taskId: string): Promise<DraftTaskStatusResponse> {
  return request(`/topics/tasks/${taskId}`);
}

export async function deleteTopic(topicId: number): Promise<MessageResponse> {
  return request(`/topics/${topicId}`, { method: 'DELETE' });
}

// ---------------------------------------------------------------------------
// Drafts
// ---------------------------------------------------------------------------

export async function fetchDrafts(params?: { platform?: string; status?: string; limit?: string; offset?: string }): Promise<Article[]> {
  const qs = new URLSearchParams(params as Record<string, string>).toString();
  return request(`/drafts${qs ? `?${qs}` : ''}`);
}

export async function fetchDraft(id: number): Promise<Article> {
  return request(`/drafts/${id}`);
}

export async function updateDraft(id: number, data: Partial<Article>): Promise<Article> {
  return request(`/drafts/${id}`, { method: 'PUT', body: JSON.stringify(data) });
}

export async function approveDraft(id: number): Promise<Article> {
  return request(`/drafts/${id}/approve`, { method: 'POST' });
}

export async function rejectDraft(id: number, reason?: string): Promise<Article> {
  return request(`/drafts/${id}/reject`, { method: 'POST', body: JSON.stringify({ reason }) });
}

export async function publishDraft(id: number): Promise<Article> {
  return request(`/drafts/${id}/publish`, { method: 'POST' });
}

export async function publishSocial(id: number): Promise<SocialPublishResponse> {
  return request(`/drafts/${id}/social/publish`, { method: 'POST' });
}

export async function regenerateDraft(id: number): Promise<Article> {
  return request(`/drafts/${id}/regenerate`, { method: 'POST' });
}

export async function deleteDraft(id: number): Promise<MessageResponse> {
  return request(`/drafts/${id}`, { method: 'DELETE' });
}

// ---------------------------------------------------------------------------
// Published
// ---------------------------------------------------------------------------

export async function fetchPublished(): Promise<PublishedArticle[]> {
  return request('/published');
}

// ---------------------------------------------------------------------------
// Audit
// ---------------------------------------------------------------------------

export async function fetchAudit(): Promise<unknown[]> {
  return request('/audit');
}

// ---------------------------------------------------------------------------
// Performance
// ---------------------------------------------------------------------------

export async function fetchPerformance(platform?: string, days?: number): Promise<PerformanceMetrics> {
  const qs = new URLSearchParams();
  if (platform) qs.set('platform', platform);
  if (days) qs.set('days', String(days));
  return request(`/performance${qs.toString() ? `?${qs}` : ''}`);
}

export async function fetchPerformanceInsights(platform?: string): Promise<PerformanceInsight> {
  const qs = platform ? `?platform=${platform}` : '';
  return request(`/performance/insights${qs}`);
}

// ---------------------------------------------------------------------------
// Paraphraser
// ---------------------------------------------------------------------------

export async function paraphraseContent(content: string, style?: string, tone?: string): Promise<{ original: string; paraphrased: string }> {
  return request('/paraphrase', {
    method: 'POST',
    body: JSON.stringify({ content, style, tone }),
  });
}

// ---------------------------------------------------------------------------
// Repurpose
// ---------------------------------------------------------------------------

export async function repurposeContent(data: {
  content: string;
  source_type: string;
  target_formats: string[];
}): Promise<RepurposeResponse> {
  return request('/repurpose', { method: 'POST', body: JSON.stringify(data) });
}

// ---------------------------------------------------------------------------
// Scoring
// ---------------------------------------------------------------------------

export async function scoreContent(articleId: number): Promise<ContentScoreResponse> {
  return request(`/scoring/${articleId}`, { method: 'POST' });
}

// ---------------------------------------------------------------------------
// Daily Posts
// ---------------------------------------------------------------------------

export async function generateDailyPosts(data: {
  industry: string;
  region?: string;
  target_audience: string;
  business_goal?: string;
}): Promise<DailyPostBatch> {
  return request('/daily-posts/generate', { method: 'POST', body: JSON.stringify(data) });
}

export async function fetchDailyPostsHistory(): Promise<DailyPostBatch[]> {
  return request('/daily-posts/history');
}

// ---------------------------------------------------------------------------
// Platform Content
// ---------------------------------------------------------------------------

export async function generatePlatformContent(data: {
  topic: string;
  platform: string;
  content_type: string;
}): Promise<PlatformContentResponse> {
  return request('/platform-content/generate', { method: 'POST', body: JSON.stringify(data) });
}

export async function fetchPlatformContentHistory(): Promise<PlatformContentResponse[]> {
  return request('/platform-content/history');
}

export async function publishPlatformContent(id: number, imageUrl?: string): Promise<{ id: number; platform: string; status: string; external_id?: string }> {
  return request(`/platform-content/${id}/publish`, {
    method: 'POST',
    body: JSON.stringify({ image_url: imageUrl ?? null }),
  });
}

// ---------------------------------------------------------------------------
// Thought Leadership
// ---------------------------------------------------------------------------

export async function generateThoughtLeadership(data: {
  topic: string;
  content_type: string;
  industry: string;
}): Promise<ThoughtLeadershipResponse> {
  return request('/thought-leadership/generate', { method: 'POST', body: JSON.stringify(data) });
}

export async function fetchThoughtLeadershipHistory(): Promise<ThoughtLeadershipResponse[]> {
  return request('/thought-leadership/history');
}

// ---------------------------------------------------------------------------
// Audience Content
// ---------------------------------------------------------------------------

export async function generateAudienceContent(data: {
  audience_type: string;
  region: string;
  income_bracket: string;
  awareness_stage: string;
  pain_points: string[];
}): Promise<AudienceContentResponse> {
  return request('/audience-content/generate', { method: 'POST', body: JSON.stringify(data) });
}

// ---------------------------------------------------------------------------
// YouTube Shorts
// ---------------------------------------------------------------------------

export async function generateYoutubeShort(data: {
  topic: string;
  target_audience?: string;
  duration?: number;
}): Promise<YoutubeShortResponse> {
  return request('/youtube-shorts/generate', { method: 'POST', body: JSON.stringify(data) });
}

export async function fetchYoutubeShortsHistory(): Promise<YoutubeShortResponse[]> {
  return request('/youtube-shorts/history');
}

// ---------------------------------------------------------------------------
// Campaigns
// ---------------------------------------------------------------------------

export async function fetchCampaigns(): Promise<Campaign[]> {
  return request('/campaigns');
}

export async function fetchCampaign(id: number): Promise<Campaign> {
  return request(`/campaigns/${id}`);
}

export async function createCampaign(data: {
  title: string;
  event_date?: string;
  goal?: string;
  audience?: string;
  platforms?: string[];
  platform_entity: string;
}): Promise<Campaign> {
  return request('/campaigns', { method: 'POST', body: JSON.stringify(data) });
}

export async function generateCampaignContent(campaignId: number): Promise<unknown> {
  return request(`/campaigns/${campaignId}/generate`, { method: 'POST' });
}

// ---------------------------------------------------------------------------
// Competitors
// ---------------------------------------------------------------------------

export async function fetchCompetitors(): Promise<Competitor[]> {
  return request('/competitors');
}

export async function fetchCompetitor(id: number): Promise<Competitor> {
  return request(`/competitors/${id}`);
}

export async function addCompetitor(data: {
  name: string;
  platform: string;
  profile_url: string;
  platform_entity: string;
}): Promise<Competitor> {
  return request('/competitors', { method: 'POST', body: JSON.stringify(data) });
}

export async function analyzeCompetitor(id: number): Promise<CompetitorAnalysis> {
  return request(`/competitors/${id}/analyze`, { method: 'POST' });
}

export async function fetchCompetitorAnalyses(id: number): Promise<CompetitorAnalysisStored[]> {
  return request(`/competitors/${id}/analyses`);
}

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

export async function fetchHooks(params?: { category?: string; platform?: string }): Promise<HookTemplate[]> {
  const qs = new URLSearchParams(params as Record<string, string>).toString();
  return request(`/hooks${qs ? `?${qs}` : ''}`);
}

export async function fetchHook(id: number): Promise<HookTemplate> {
  return request(`/hooks/${id}`);
}

export async function createHook(data: {
  hook_text: string;
  category: string;
  platform: string;
  industry?: string;
}): Promise<HookTemplate> {
  return request('/hooks', { method: 'POST', body: JSON.stringify(data) });
}

export async function suggestHooks(topic: string, platform?: string, count?: number): Promise<HookSuggestionResponse> {
  const qs = new URLSearchParams({ topic, ...(platform ? { platform } : {}), ...(count ? { count: String(count) } : {}) });
  return request(`/hooks/suggest?${qs}`);
}

// ---------------------------------------------------------------------------
// Swipe Files
// ---------------------------------------------------------------------------

export async function fetchSwipeFiles(): Promise<SwipeFile[]> {
  return request('/swipe-files');
}

export async function fetchSwipeFile(id: number): Promise<SwipeFile> {
  return request(`/swipe-files/${id}`);
}

export async function createSwipeFile(data: {
  platform: string;
  title: string;
  content: string;
  source_url?: string;
  performance_notes?: string;
  tags?: string[];
}): Promise<SwipeFile> {
  return request('/swipe-files', { method: 'POST', body: JSON.stringify(data) });
}

export async function deleteSwipeFile(id: number): Promise<void> {
  return request(`/swipe-files/${id}`, { method: 'DELETE' });
}

// ---------------------------------------------------------------------------
// Scheduling
// ---------------------------------------------------------------------------

export async function fetchScheduledPosts(params?: { platform?: string; status?: string }): Promise<ScheduledPost[]> {
  const qs = new URLSearchParams(params as Record<string, string>).toString();
  return request(`/scheduling${qs ? `?${qs}` : ''}`);
}

export async function createScheduledPost(data: ScheduledPostCreate): Promise<ScheduledPost> {
  return request('/scheduling', { method: 'POST', body: JSON.stringify(data) });
}

export async function updateScheduledPost(id: number, data: Partial<ScheduledPost>): Promise<ScheduledPost> {
  return request(`/scheduling/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
}

export async function deleteScheduledPost(id: number): Promise<void> {
  return request(`/scheduling/${id}`, { method: 'DELETE' });
}

export async function fetchCalendarStats(): Promise<CalendarStats> {
  return request('/scheduling/stats');
}

// ---------------------------------------------------------------------------
// Social Accounts
// ---------------------------------------------------------------------------

export async function fetchSocialAccounts(): Promise<SocialAccount[]> {
  return request('/social-accounts');
}

export async function startSocialOAuth(platform: string): Promise<{ platform: string; configured: boolean; auth_url?: string; setup_url?: string }> {
  return request(`/social-accounts/oauth/${platform}/start`);
}

export async function removeSocialAccount(id: number): Promise<void> {
  return request(`/social-accounts/${id}`, { method: 'DELETE' });
}

export async function publishToSocial(content: string, platform: string, imageUrl?: string): Promise<{ platform: string; status: string; external_id?: string }> {
  return request('/social-accounts/publish', {
    method: 'POST',
    body: JSON.stringify({ content, platform, image_url: imageUrl ?? null }),
  });
}

export async function uploadImage(imageData: string): Promise<{ url: string; public_id: string }> {
  return request('/images/upload', {
    method: 'POST',
    body: JSON.stringify({ image_data: imageData }),
  });
}

// ---------------------------------------------------------------------------
// Regional
// ---------------------------------------------------------------------------

export async function localiseContent(data: {
  content: string;
  region: string;
  language_style?: string;
}): Promise<LocaliseResponse> {
  return request('/regional/localise', { method: 'POST', body: JSON.stringify(data) });
}

export async function fetchRegionalTrendingTopics(data: {
  region: string;
  industry: string;
  time_frame?: string;
}): Promise<RegionalTrendingResponse> {
  return request('/regional/trending-topics', { method: 'POST', body: JSON.stringify(data) });
}

export async function fetchRegionalHashtags(data: {
  region: string;
  topic: string;
  platform?: string;
}): Promise<RegionalHashtagResponse> {
  return request('/regional/hashtags', { method: 'POST', body: JSON.stringify(data) });
}

export async function fetchRegionalHistory(): Promise<RegionalHistoryItem[]> {
  return request('/regional/history');
}

// ---------------------------------------------------------------------------
// Image Text Extraction
// ---------------------------------------------------------------------------

export async function extractImageText(data: {
  content: string;
  platform: string;
  template_type?: string;
}): Promise<{ image_text: string }> {
  return request('/image-text/extract', { method: 'POST', body: JSON.stringify(data) });
}

// ---------------------------------------------------------------------------
// AI Image Generation
// ---------------------------------------------------------------------------

export async function generateAIImage(articleId: number, platform: string): Promise<{ image_url: string; platform: string; article_id: number }> {
  return request('/ai-images/generate', {
    method: 'POST',
    body: JSON.stringify({ article_id: articleId, platform }),
  });
}

export async function generateAIImageFromText(data: {
  caption: string;
  platform: string;
  title?: string;
  context?: string;
}): Promise<{ image_url: string; platform: string }> {
  return request('/ai-images/generate-from-text', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
