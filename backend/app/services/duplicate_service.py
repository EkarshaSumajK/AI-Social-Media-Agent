from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.topic import Topic
from app.services.embeddings_service import EmbeddingsClient, cosine_similarity

settings = get_settings()


class DuplicateChecker:
    def __init__(self, embeddings_client: EmbeddingsClient | None = None) -> None:
        self.embeddings = embeddings_client or EmbeddingsClient()

    async def check_topic(
        self,
        db: AsyncSession,
        *,
        title: str,
        summary: str | None,
        threshold: float | None = None,
    ) -> tuple[bool, float, int | None, list[float]]:
        probe = f'{title}\n{summary or ""}'
        probe_embedding = await self.embeddings.embed(probe)

        result = await db.execute(
            select(Topic.id, Topic.embedding).where(Topic.embedding.is_not(None)).order_by(Topic.created_at.desc()).limit(250)
        )

        best_score = 0.0
        best_topic_id: int | None = None
        for topic_id, embedding in result.all():
            if not embedding:
                continue
            score = cosine_similarity(probe_embedding, list(embedding))
            if score > best_score:
                best_score = score
                best_topic_id = topic_id

        score_threshold = threshold if threshold is not None else settings.duplicate_similarity_threshold
        is_duplicate = best_score >= score_threshold
        return is_duplicate, best_score, best_topic_id, probe_embedding
