# Enum to String Migration

## Overview
Converted all SQLAlchemy Enum fields to String fields to ensure compatibility with existing database values that use mixed case (lowercase and uppercase).

## Problem
The database contained enum values in mixed case:
- UserRole: 'admin', 'reviewer', 'ADMIN', 'COUNSELLOR', etc.
- TopicStatus: 'new', 'NEW', 'processed', 'PROCESSED', 'duplicate_rejected', 'DUPLICATE_REJECTED'
- ArticleStatus: 'draft', 'approved', 'rejected', 'published'
- SocialStatus: 'draft', 'ready', 'posted', 'failed'
- Platform: 'horizon', 'connect', 'parentshala'

SQLAlchemy's Enum validation was rejecting lowercase values like 'admin' and 'new' because the Python enums defined uppercase values.

## Solution
Converted all enum fields to String fields with appropriate length constraints:
- `Enum(EnumType)` → `String(50)`
- Updated all code to use string literals instead of enum values
- Removed enum imports from all service and route files

## Files Modified

### Models (Enum → String conversion)
- `app/models/user.py` - role, platform fields
- `app/models/article.py` - status, platform fields
- `app/models/topic.py` - status, platform fields
- `app/models/social_post.py` - status, platform fields

### Services (Enum value → String literal)
- `app/services/content_pipeline_service.py`
- `app/services/article_service.py`
- `app/services/trend_collector_service.py`
- `app/services/social_service.py`
- `app/services/user_service.py`

### Routes (Enum value → String literal)
- `app/api/routes/topics.py`
- `app/api/routes/drafts.py`
- `app/api/routes/published.py`
- `app/api/routes/audit.py`
- `app/api/routes/platform_content.py`
- `app/api/routes/social_accounts.py`
- `app/api/deps.py`

## String Values Used

### User Roles
- 'admin' (lowercase - matches existing data)
- 'reviewer'
- 'ADMIN' (uppercase - also in database)
- Other roles as strings

### Topic Status
- 'new' (lowercase - matches existing data)
- 'processed'
- 'duplicate_rejected'

### Article Status
- 'draft'
- 'approved'
- 'rejected'
- 'published'

### Social Status
- 'draft'
- 'ready'
- 'posted'
- 'failed'

### Platform
- 'horizon'
- 'connect'
- 'parentshala'
- 'instagram'
- 'linkedin'
- 'twitter'
- 'facebook'

## Benefits
1. No more enum validation errors with existing database data
2. Flexible - can accept any case variation
3. No need for database migrations to change enum values
4. Simpler code - direct string comparisons instead of enum lookups
5. Preserves all existing data without modification

## Notes
- The `app/models/enums.py` file is kept for reference but no longer imported
- All string comparisons are case-sensitive
- Database constraints remain unchanged (existing data preserved)
