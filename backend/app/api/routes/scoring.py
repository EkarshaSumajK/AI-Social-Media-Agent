from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_reviewer
from app.core.database import get_db
from app.models.user import User
from app.schemas.article import ContentScoreResponse
from app.services.article_service import ArticleService
from app.services.content_scoring_service import ContentScoringService

router = APIRouter()
_article_service = ArticleService()
_scoring_service = ContentScoringService()


@router.post('/{article_id}', response_model=ContentScoreResponse)
async def score_article(
    article_id: int,
    current_user: User = Depends(get_current_reviewer),
    db: AsyncSession = Depends(get_db),
) -> ContentScoreResponse:
    try:
        article = await _article_service.get_article(db, article_id)
    except ValueError:
        raise HTTPException(status_code=404, detail='Article not found')

    scores = await _scoring_service.score_content(
        title=article.seo_title,
        content=article.content_html,
    )

    article.virality_score = scores['virality_score']
    article.clarity_score = scores['clarity_score']
    article.hook_strength_score = scores['hook_strength_score']
    article.conversion_score = scores['conversion_score']
    await db.commit()

    return ContentScoreResponse(
        article_id=article.id,
        virality_score=scores['virality_score'],
        clarity_score=scores['clarity_score'],
        hook_strength_score=scores['hook_strength_score'],
        conversion_score=scores['conversion_score'],
        breakdown=scores.get('breakdown', {}),
    )
