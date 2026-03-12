from __future__ import annotations

from app.services.llm_service import LLMClient
from app.services.prompt_service import get_prompt_catalog


class ParaphraserService:
    def __init__(self) -> None:
        self.llm = LLMClient()
        self.prompts = get_prompt_catalog()

    async def paraphrase(
        self,
        *,
        content: str,
        style: str = 'professional',
        tone: str = 'supportive and clear',
    ) -> str:
        system_prompt, prompt = self.prompts.get_prompt(
            bundle='paraphraser/v1/prompts.yaml',
            key='paraphrase_content',
            context={
                'content': content,
                'style': style,
                'tone': tone,
            },
        )
        result = await self.llm.generate(
            system_prompt=system_prompt,
            prompt=prompt,
            temperature=0.5,
        )
        return result.strip()
