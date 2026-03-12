from __future__ import annotations

from app.services.llm_service import LLMClient
from app.services.prompt_service import get_prompt_catalog


class ContentScoringService:
    def __init__(self) -> None:
        self.llm = LLMClient()
        self.prompts = get_prompt_catalog()

    async def score_content(self, *, title: str, content: str) -> dict:
        system_prompt, prompt = self.prompts.get_prompt(
            bundle='content_scoring/v1/prompts.yaml',
            key='score_content',
            context={'title': title, 'content': content[:6000]},
        )
        result = await self.llm.generate_json(
            system_prompt=system_prompt,
            prompt=prompt,
            temperature=0.2,
        )
        if not result:
            return {
                'virality_score': 0,
                'clarity_score': 0,
                'hook_strength_score': 0,
                'conversion_score': 0,
                'overall_score': 0,
                'breakdown': {},
            }
        return {
            'virality_score': min(100, max(0, int(result.get('virality_score', 0)))),
            'clarity_score': min(100, max(0, int(result.get('clarity_score', 0)))),
            'hook_strength_score': min(100, max(0, int(result.get('hook_strength_score', 0)))),
            'conversion_score': min(100, max(0, int(result.get('conversion_score', 0)))),
            'overall_score': min(100, max(0, int(result.get('overall_score', 0)))),
            'breakdown': result.get('breakdown', {}),
        }
