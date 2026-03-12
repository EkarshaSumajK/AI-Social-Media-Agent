from fastapi import APIRouter, Depends

from app.api.deps import get_current_reviewer
from app.models.user import User
from app.schemas.article import ParaphraseRequest, ParaphraseResponse
from app.services.paraphraser_service import ParaphraserService

router = APIRouter()
_service = ParaphraserService()


@router.post('', response_model=ParaphraseResponse)
async def paraphrase_content(
    payload: ParaphraseRequest,
    _: User = Depends(get_current_reviewer),
) -> ParaphraseResponse:
    result = await _service.paraphrase(
        content=payload.content,
        style=payload.style,
        tone=payload.tone,
    )
    return ParaphraseResponse(original=payload.content, paraphrased=result)
