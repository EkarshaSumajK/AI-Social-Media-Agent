from enum import Enum


class TopicStatus(str, Enum):
    NEW = 'NEW'
    PROCESSED = 'PROCESSED'
    DUPLICATE_REJECTED = 'DUPLICATE_REJECTED'


class ArticleStatus(str, Enum):
    DRAFT = 'DRAFT'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    PUBLISHED = 'PUBLISHED'


class SocialPlatform(str, Enum):
    INSTAGRAM = 'INSTAGRAM'
    LINKEDIN = 'LINKEDIN'
    TWITTER = 'TWITTER'
    FACEBOOK = 'FACEBOOK'


class SocialStatus(str, Enum):
    DRAFT = 'DRAFT'
    READY = 'READY'
    POSTED = 'POSTED'
    FAILED = 'FAILED'


class UserRole(str, Enum):
    COUNSELLOR = 'COUNSELLOR'
    REVIEWER = 'reviewer'
    TEACHER = 'TEACHER'
    ADMIN = 'admin'  # lowercase admin (matches existing data)
    PRINCIPAL = 'PRINCIPAL'
    PARENT = 'PARENT'
    CLINICIAN = 'CLINICIAN'
    ADMIN_UPPER = 'ADMIN'  # uppercase admin
    STUDENT = 'STUDENT'
    OWNER = 'OWNER'


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
    INDIA = 'INDIA'
    USA = 'USA'
    GLOBAL = 'GLOBAL'


class CampaignStatus(str, Enum):
    DRAFT = 'draft'
    ACTIVE = 'active'
    COMPLETED = 'completed'


class CampaignPhase(str, Enum):
    PRE = 'pre'
    DURING = 'during'
    POST = 'post'
