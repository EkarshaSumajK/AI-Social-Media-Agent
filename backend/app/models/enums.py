from enum import Enum


class TopicStatus(str, Enum):
    NEW = 'new'
    PROCESSED = 'processed'
    DUPLICATE_REJECTED = 'duplicate_rejected'


class ArticleStatus(str, Enum):
    DRAFT = 'draft'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    PUBLISHED = 'published'


class SocialPlatform(str, Enum):
    INSTAGRAM = 'instagram'
    LINKEDIN = 'linkedin'
    TWITTER = 'twitter'
    FACEBOOK = 'facebook'


class SocialStatus(str, Enum):
    DRAFT = 'draft'
    READY = 'ready'
    POSTED = 'posted'
    FAILED = 'failed'


class UserRole(str, Enum):
    REVIEWER = 'reviewer'
    ADMIN = 'admin'


class Platform(str, Enum):
    HORIZON = 'horizon'
    CONNECT = 'connect'
    PARENTSHALA = 'parentshala'


class TopicCategory(str, Enum):
    BUSINESS = 'business'
    MARKETING = 'marketing'
    AI = 'ai'
    ECONOMY = 'economy'
    POLITICS = 'politics'
    STARTUPS = 'startups'
    CREATOR_ECONOMY = 'creator_economy'
    TECHNOLOGY = 'technology'
    HEALTH = 'health'


class Region(str, Enum):
    INDIA = 'india'
    USA = 'usa'
    GLOBAL = 'global'


class CampaignStatus(str, Enum):
    DRAFT = 'draft'
    ACTIVE = 'active'
    COMPLETED = 'completed'


class CampaignPhase(str, Enum):
    PRE = 'pre'
    DURING = 'during'
    POST = 'post'
