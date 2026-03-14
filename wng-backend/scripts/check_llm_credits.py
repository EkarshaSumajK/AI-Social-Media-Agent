import asyncio
import sys
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings


def _extract_error(exc: Exception) -> tuple[int | None, str, str]:
    status_code = getattr(exc, 'status_code', None)
    code = ''
    message = str(exc)

    body: Any = getattr(exc, 'body', None)
    if isinstance(body, dict):
        payload = body.get('error') if isinstance(body.get('error'), dict) else body
        if isinstance(payload, dict):
            code = str(payload.get('code') or '').strip()
            msg = payload.get('message')
            if msg:
                message = str(msg)

    lowered = message.lower()
    if not code:
        if 'insufficient_quota' in lowered:
            code = 'insufficient_quota'
        elif 'billing_hard_limit_reached' in lowered:
            code = 'billing_hard_limit_reached'
        elif 'invalid_api_key' in lowered:
            code = 'invalid_api_key'
        elif 'model_not_found' in lowered:
            code = 'model_not_found'

    return status_code, code, message


def _is_quota_error(status_code: int | None, code: str, message: str) -> bool:
    lowered = message.lower()
    return (
        code in {'insufficient_quota', 'billing_hard_limit_reached'}
        or (status_code == 429 and ('quota' in lowered or 'billing' in lowered))
    )


async def _check_chat(client: AsyncOpenAI, model: str) -> tuple[bool, str]:
    try:
        await client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': 'You are a health check probe.'},
                {'role': 'user', 'content': 'Reply with OK only.'},
            ],
        )
        return True, f'PASS: Chat completion works with model "{model}".'
    except Exception as exc:  # noqa: BLE001
        status_code, code, message = _extract_error(exc)
        if _is_quota_error(status_code, code, message):
            return False, f'FAIL: No LLM credits (status={status_code}, code={code or "n/a"}).'
        return False, (
            f'FAIL: Chat check failed (status={status_code}, code={code or "n/a"}): {message}'
        )


async def _check_embeddings(client: AsyncOpenAI, model: str) -> tuple[bool, str]:
    try:
        await client.embeddings.create(model=model, input='credit-check')
        return True, f'PASS: Embeddings work with model "{model}".'
    except Exception as exc:  # noqa: BLE001
        status_code, code, message = _extract_error(exc)
        if _is_quota_error(status_code, code, message):
            return False, f'FAIL: No credits for embeddings (status={status_code}, code={code or "n/a"}).'
        return False, (
            f'FAIL: Embeddings check failed (status={status_code}, code={code or "n/a"}): {message}'
        )


async def main() -> None:
    settings = get_settings()
    if not settings.llm_api_key:
        print('FAIL: LLM_API_KEY is missing in .env')
        raise SystemExit(1)

    client = AsyncOpenAI(api_key=settings.llm_api_key)

    chat_ok, chat_msg = await _check_chat(client, settings.llm_model)
    print(chat_msg)

    emb_ok, emb_msg = await _check_embeddings(client, settings.embeddings_model)
    print(emb_msg)

    if chat_ok:
        print('RESULT: Credits and model access look OK for chat generation.')
        raise SystemExit(0)

    if not chat_ok and not emb_ok:
        if 'No LLM credits' in chat_msg or 'No credits for embeddings' in emb_msg:
            print('RESULT: Credits are unavailable or exhausted.')
            raise SystemExit(2)
        print('RESULT: API key/model/config issue (not a clear credit failure).')
        raise SystemExit(1)

    if emb_ok and not chat_ok:
        print('RESULT: Credits likely exist, but chat model access/config failed.')
        raise SystemExit(1)

    print('RESULT: Unexpected mixed state.')
    raise SystemExit(1)


if __name__ == '__main__':
    asyncio.run(main())
