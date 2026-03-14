import argparse
import asyncio
import json
import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings
from app.services.trend_collector_service import (
    _compose_x_discovery_query,
    _strip_pro_only_operators,
)

X_SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"
PRO_RESTRICTED_TOKENS = (
    "place_country:",
    "has:geo",
    "min_faves:",
    "min_retweets:",
    "min_replies:",
)


def _contains_restricted_operator(query: str) -> bool:
    normalized = str(query or "").lower()
    return any(token in normalized for token in PRO_RESTRICTED_TOKENS)


def _build_search_params(search_query: str, max_results: int) -> dict[str, str | int]:
    return {
        "query": search_query,
        "max_results": max_results,
        "tweet.fields": "author_id,created_at,entities,geo,lang,public_metrics,text",
        "expansions": "author_id,geo.place_id",
        "user.fields": "created_at,public_metrics,verified",
        "place.fields": "country_code",
    }


def _extract_error_detail(payload: object) -> str:
    if not isinstance(payload, dict):
        return str(payload)
    errors = payload.get("errors")
    if isinstance(errors, list) and errors:
        first = errors[0]
        if isinstance(first, dict):
            detail = str(first.get("message") or first.get("detail") or "").strip()
            if detail:
                return detail
    detail = str(payload.get("detail") or payload.get("title") or "").strip()
    if detail:
        return detail
    return json.dumps(payload)[:800]


async def _check_query(
    *,
    client: httpx.AsyncClient,
    headers: dict[str, str],
    label: str,
    query: str,
    max_results: int,
) -> tuple[bool, str]:
    try:
        response = await client.get(
            X_SEARCH_URL,
            params=_build_search_params(search_query=query, max_results=max_results),
            headers=headers,
        )
    except Exception as exc:
        return False, f"{label}: request failed: {exc}"

    payload: object
    try:
        payload = response.json()
    except Exception:
        payload = response.text

    if response.status_code == 200:
        data_count = len(payload.get("data") or []) if isinstance(payload, dict) else 0
        return True, f"{label}: PASS HTTP 200 (tweets={data_count})"

    detail = _extract_error_detail(payload)
    return False, f"{label}: FAIL HTTP {response.status_code} ({detail})"


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Quick compatibility check for X API recent-search queries used by the pipeline."
    )
    parser.add_argument(
        "--query",
        default="child mental health",
        help="Seed query for compose/sanitize checks.",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="max_results passed to X recent search endpoint (1-100).",
    )
    args = parser.parse_args()

    max_results = max(1, min(100, int(args.max_results)))
    settings = get_settings()

    base_composed = _compose_x_discovery_query(args.query)
    sanitized_composed = _strip_pro_only_operators(base_composed)

    restricted_query = (
        f"({args.query}) lang:en -is:retweet "
        "(place_country:IN OR place_country:US) has:geo min_faves:25 min_retweets:5 min_replies:2"
    )
    sanitized_restricted = _strip_pro_only_operators(restricted_query)

    print("X API Query Compatibility Check")
    print(f"- Compose query: {base_composed}")
    print(f"- Compose query has restricted operators: {_contains_restricted_operator(base_composed)}")
    print(f"- Sanitized compose query: {sanitized_composed}")
    print(f"- Restricted test query: {restricted_query}")
    print(f"- Sanitized restricted query: {sanitized_restricted}")
    print(f"- Sanitized restricted has restricted operators: {_contains_restricted_operator(sanitized_restricted)}")

    if not settings.x_bearer_token:
        print("FAIL: X_BEARER_TOKEN is missing in .env; skipped live API checks.")
        raise SystemExit(1)

    headers = {"Authorization": f"Bearer {settings.x_bearer_token}"}
    async with httpx.AsyncClient(timeout=20.0) as client:
        checks = await asyncio.gather(
            _check_query(
                client=client,
                headers=headers,
                label="Current pipeline composed query",
                query=sanitized_composed,
                max_results=max_results,
            ),
            _check_query(
                client=client,
                headers=headers,
                label="Intentionally restricted query (expected to fail on basic plan)",
                query=restricted_query,
                max_results=max_results,
            ),
            _check_query(
                client=client,
                headers=headers,
                label="Sanitized restricted query (basic-plan safe)",
                query=sanitized_restricted,
                max_results=max_results,
            ),
        )

    all_passed = True
    for ok, message in checks:
        print(message)
        if not ok and "Intentionally restricted query" not in message:
            all_passed = False

    restricted_failed = not checks[1][0]
    sanitized_passed = checks[2][0]

    if restricted_failed and sanitized_passed:
        print("PASS: Country/pro-only operators are the likely rejection source; sanitizer path works.")
    elif not restricted_failed:
        print("INFO: Restricted query did not fail in this environment/account.")
    else:
        print("WARN: Sanitized query still failed; check token permissions/rate limits/network.")

    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
