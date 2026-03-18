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

VALID_PLATFORMS = {p.value for p in SocialPlatform}


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
        image_url = await service.generate_and_upload(
            platform=payload.platform.lower(),
            caption=caption,
            article_title=article.seo_title or '',
            article_summary=article_summary,
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
    if payload.platform not in VALID_PLATFORMS:
        raise HTTPException(status_code=400, detail=f'Invalid platform. Must be one of: {", ".join(sorted(VALID_PLATFORMS))}')

    caption = payload.caption.strip()
    if not caption:
        raise HTTPException(status_code=400, detail='Caption text is required')

    try:
        service = ImageService()
        image_url = await service.generate_and_upload(
            platform=payload.platform.lower(),
            caption=caption,
            article_title=payload.title.strip() or 'Mental Health Awareness',
            article_summary=payload.context.strip(),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f'Image generation failed: {exc}') from exc

    return GenerateFromTextResponse(
        image_url=image_url,
        platform=payload.platform,
    )
