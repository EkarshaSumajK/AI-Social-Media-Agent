from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_reviewer
from app.core.database import get_db
from app.models.article import Article
from app.models.enums import SocialPlatform
from app.models.social_post import SocialPost
from app.models.user import User
from app.services.image_service import ImageService

router = APIRouter()

VALID_PLATFORMS = {p.value for p in SocialPlatform} | {'ARTICLE_BODY'}
VALID_FIELD_KEYS = {
    'issue_summary',
    'why_it_matters',
    'mental_health_implications',
    'professional_insight',
    'how_services_help',
    'call_to_action',
}


class GenerateAIImageRequest(BaseModel):
    article_id: int
    platform: str


class GenerateAIImageResponse(BaseModel):
    image_url: str
    platform: str
    article_id: int


@router.post('/generate', response_model=GenerateAIImageResponse)
async def generate_ai_image(
    payload: GenerateAIImageRequest,
    current_user: User = Depends(get_current_reviewer),
    db: AsyncSession = Depends(get_db),
) -> GenerateAIImageResponse:
    """Generate a platform-specific AI image for a social post and upload to Cloudinary."""
    if payload.platform not in VALID_PLATFORMS:
        raise HTTPException(status_code=400, detail=f'Invalid platform. Must be one of: {", ".join(sorted(VALID_PLATFORMS))}')

    result = await db.execute(
        select(Article)
        .options(selectinload(Article.social_posts))
        .where(Article.id == payload.article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail='Article not found')

    social_post: SocialPost | None = None
    for sp in article.social_posts:
        if sp.platform.value == payload.platform:
            social_post = sp
            break

    if not social_post:
        raise HTTPException(status_code=404, detail=f'No social post found for platform: {payload.platform}')

    caption = (social_post.edited_caption or social_post.caption or '').strip()
    if not caption:
        raise HTTPException(status_code=400, detail='Social post has no caption to use as context')

    # Build article summary from available sections for richer infographic content
    summary_parts = [
        article.issue_summary or '',
        article.why_it_matters or '',
        article.professional_insight or '',
        article.call_to_action or '',
    ]
    article_summary = ' '.join(part.strip() for part in summary_parts if part.strip())[:2000]

    try:
        service = ImageService()
        # Create unique context to differentiate images for different articles
        unique_context = f"Article ID: {article.id}, Platform: {payload.platform}, Topic: {article.seo_title[:100]}"
        image_url = await service.generate_and_upload(
            platform=payload.platform.lower(),
            caption=caption,
            article_title=article.seo_title or '',
            article_summary=article_summary,
            unique_context=unique_context,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f'Image generation failed: {exc}') from exc

    social_post.image_url = image_url
    await db.commit()

    return GenerateAIImageResponse(
        image_url=image_url,
        platform=payload.platform,
        article_id=payload.article_id,
    )


class GenerateFromTextRequest(BaseModel):
    caption: str
    platform: str
    title: str = ''
    context: str = ''


class GenerateFromTextResponse(BaseModel):
    image_url: str
    platform: str


@router.post('/generate-from-text', response_model=GenerateFromTextResponse)
async def generate_ai_image_from_text(
    payload: GenerateFromTextRequest,
    current_user: User = Depends(get_current_reviewer),
) -> GenerateFromTextResponse:
    """Generate a platform-specific AI infographic from raw text content. No article required."""
    # Normalize platform to uppercase for validation
    platform_upper = payload.platform.upper()
    if platform_upper not in VALID_PLATFORMS:
        raise HTTPException(status_code=400, detail=f'Invalid platform. Must be one of: {", ".join(sorted(VALID_PLATFORMS))}')

    caption = payload.caption.strip()
    if not caption:
        raise HTTPException(status_code=400, detail='Caption text is required')

    try:
        service = ImageService()
        # Create unique context for standalone text generation
        import time
        unique_context = f"Generated at: {int(time.time())}, Platform: {platform_upper}"
        image_url = await service.generate_and_upload(
            platform=platform_upper.lower(),  # ImageService expects lowercase
            caption=caption,
            article_title=payload.title.strip() or 'Mental Health Awareness',
            article_summary=payload.context.strip(),
            unique_context=unique_context,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f'Image generation failed: {exc}') from exc

    return GenerateFromTextResponse(
        image_url=image_url,
        platform=payload.platform,
    )


class GenerateArticleFieldImageRequest(BaseModel):
    article_id: int
    field_key: str


class GenerateArticleFieldImageResponse(BaseModel):
    image_url: str
    field_key: str
    article_id: int


@router.post('/generate-article-field', response_model=GenerateArticleFieldImageResponse)
async def generate_article_field_image(
    payload: GenerateArticleFieldImageRequest,
    current_user: User = Depends(get_current_reviewer),
    db: AsyncSession = Depends(get_db),
) -> GenerateArticleFieldImageResponse:
    """Generate an infographic for an article body or structured field and persist the URL."""
    field_key = payload.field_key.strip()

    if field_key == 'content_html':
        target = 'body'
    elif field_key in VALID_FIELD_KEYS:
        target = 'field'
    else:
        raise HTTPException(
            status_code=400,
            detail=f'Invalid field_key. Use "content_html" or one of: {", ".join(sorted(VALID_FIELD_KEYS))}',
        )

    result = await db.execute(select(Article).where(Article.id == payload.article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail='Article not found')

    if target == 'body':
        caption = _strip_html(article.content_html or '')
        if not caption:
            raise HTTPException(status_code=400, detail='Article body is empty')
        context_parts = [
            article.issue_summary or '',
            article.why_it_matters or '',
        ]
        context = ' '.join(p.strip() for p in context_parts if p.strip())[:2000]
    else:
        caption = getattr(article, field_key, '') or ''
        if not caption.strip():
            raise HTTPException(status_code=400, detail=f'Field {field_key} is empty')
        caption = caption.strip()
        context_parts = [
            article.issue_summary or '',
            article.why_it_matters or '',
            article.professional_insight or '',
            article.call_to_action or '',
        ]
        context = ' '.join(p.strip() for p in context_parts if p.strip())[:2000]

    try:
        service = ImageService()
        # Create unique context to differentiate field images
        import time
        unique_context = f"Article ID: {article.id}, Field: {field_key}, Generated: {int(time.time())}"
        image_url = await service.generate_and_upload(
            platform='article_body',
            caption=caption[:3000],
            article_title=article.seo_title or '',
            article_summary=context,
            unique_context=unique_context,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f'Image generation failed: {exc}') from exc

    if target == 'body':
        article.body_image_url = image_url
    else:
        field_urls: dict = article.field_image_urls or {}
        field_urls[field_key] = image_url
        article.field_image_urls = field_urls

    await db.commit()

    return GenerateArticleFieldImageResponse(
        image_url=image_url,
        field_key=payload.field_key,
        article_id=payload.article_id,
    )


def _strip_html(html: str) -> str:
    import re
    text = re.sub(r'<script[\s\S]*?</script>', ' ', html, flags=re.IGNORECASE)
    text = re.sub(r'<style[\s\S]*?</style>', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()
