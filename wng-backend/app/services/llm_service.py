import json
import logging
import re
import time
from typing import Any

from openai import AsyncOpenAI

from app.core.config import get_settings

settings = get_settings()
TEMPERATURE_CAPABLE_PREFIXES = (
    'gpt-4o',
    'gpt-4-turbo',
    'gpt-4',
    'gpt-3.5',
)
TEMPERATURE_BLOCKED_PREFIXES = (
    'gpt-5',
    'o1',
    'o3',
    'o4',
)
_temperature_blocklist: set[str] = set()
_llm_disabled_until_epoch: float = 0.0


class LLMClient:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.llm_api_key) if settings.llm_api_key else None

    async def generate(
        self,
        *,
        prompt: str,
        system_prompt: str,
        model: str | None = None,
        temperature: float = 0.4,
    ) -> str:
        if not self.client:
            return self._fallback(prompt)
        if _is_llm_temporarily_disabled():
            return self._fallback(prompt)

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': prompt},
        ]
        model_name = model or settings.llm_model

        try:
            if _supports_temperature(model_name):
                response = await self.client.chat.completions.create(
                    model=model_name,
                    temperature=temperature,
                    messages=messages,
                )
            else:
                response = await self.client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                )
            return response.choices[0].message.content or ''
        except Exception as exc:  # noqa: BLE001
            if _is_auth_or_quota_error(exc):
                _disable_llm_temporarily()
            if _temperature_unsupported(exc):
                _remember_temperature_unsupported(model_name)
                try:
                    response = await self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                    )
                    return response.choices[0].message.content or ''
                except Exception:  # noqa: BLE001
                    logging.warning('LLM generation fallback triggered for model %s', model_name)
                    return self._fallback(prompt)
            logging.warning('LLM generation failed for model %s: %s', model_name, exc)
            return self._fallback(prompt)

    async def generate_json(
        self,
        *,
        prompt: str,
        system_prompt: str,
        model: str | None = None,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        text = await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
        )
        candidate = _extract_json_block(text)
        if not candidate:
            return {}
        try:
            payload = json.loads(candidate)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            return {}
        return {}

    def _fallback(self, prompt: str) -> str:
        trimmed = prompt.strip().replace('\n', ' ')
        if len(trimmed) > 320:
            trimmed = trimmed[:320] + '...'
        return f'Fallback response based on prompt context: {trimmed}'


def _extract_json_block(text: str) -> str | None:
    if not text:
        return None
    stripped = text.strip()
    if stripped.startswith('{') and stripped.endswith('}'):
        return stripped

    match = re.search(r'\{.*\}', stripped, flags=re.DOTALL)
    if not match:
        return None
    return match.group(0)


def _temperature_unsupported(exc: Exception) -> bool:
    message = str(exc).lower()
    if 'temperature' in message and (
        'unsupported' in message
        or 'not supported' in message
        or 'only the default' in message
    ):
        return True
    status_code = getattr(exc, 'status_code', None)
    if status_code != 400:
        return False
    return 'temperature' in message


def _supports_temperature(model_name: str) -> bool:
    normalized = str(model_name or '').strip().lower()
    if not normalized:
        return False
    if normalized in _temperature_blocklist:
        return False
    if normalized.startswith(TEMPERATURE_BLOCKED_PREFIXES):
        return False
    return normalized.startswith(TEMPERATURE_CAPABLE_PREFIXES)


def _remember_temperature_unsupported(model_name: str) -> None:
    normalized = str(model_name or '').strip().lower()
    if normalized:
        _temperature_blocklist.add(normalized)


def _is_auth_or_quota_error(exc: Exception) -> bool:
    status_code = getattr(exc, 'status_code', None)
    return status_code in {401, 403, 429}


def _disable_llm_temporarily(seconds: float = 120.0) -> None:
    global _llm_disabled_until_epoch
    _llm_disabled_until_epoch = max(_llm_disabled_until_epoch, time.time() + seconds)


def _is_llm_temporarily_disabled() -> bool:
    return time.time() < _llm_disabled_until_epoch
