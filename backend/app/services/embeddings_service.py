import hashlib
import math
from collections import Counter

from openai import AsyncOpenAI

from app.core.config import get_settings

settings = get_settings()


class EmbeddingsClient:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.llm_api_key) if settings.llm_api_key else None

    async def embed(self, text: str) -> list[float]:
        cleaned = ' '.join(text.lower().split())
        if not cleaned:
            return [0.0] * 64

        if self._client:
            response = await self._client.embeddings.create(
                model=settings.embeddings_model,
                input=cleaned,
            )
            return response.data[0].embedding

        return self._local_embedding(cleaned)

    def _local_embedding(self, text: str, size: int = 64) -> list[float]:
        counter = Counter(text.split())
        vec = [0.0] * size
        for token, count in counter.items():
            digest = hashlib.sha256(token.encode('utf-8')).digest()
            idx = digest[0] % size
            vec[idx] += float(count)

        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    if not vector_a or not vector_b:
        return 0.0

    size = min(len(vector_a), len(vector_b))
    dot = sum(vector_a[i] * vector_b[i] for i in range(size))
    norm_a = math.sqrt(sum(v * v for v in vector_a[:size]))
    norm_b = math.sqrt(sum(v * v for v in vector_b[:size]))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
