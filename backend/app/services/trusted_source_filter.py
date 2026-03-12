from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

import yaml

from app.core.config import get_settings

settings = get_settings()


@lru_cache(maxsize=1)
def _trusted_domains() -> set[str]:
    path = Path(settings.trusted_sources_file)
    if not path.exists():
        return set()

    try:
        with path.open('r', encoding='utf-8') as handle:
            payload = yaml.safe_load(handle) or {}
    except Exception:
        return set()

    if not isinstance(payload, dict):
        return set()

    sources = payload.get('sources') or {}
    if not isinstance(sources, dict):
        return set()

    domains: set[str] = set()
    for source in sources.values():
        if not isinstance(source, dict):
            continue
        for domain in source.get('domains') or []:
            normalized = str(domain or '').strip().lower()
            if normalized:
                domains.add(normalized)
    return domains


def is_trusted_source_url(url: str | None) -> bool:
    if not url:
        return False
    domains = _trusted_domains()
    if not domains:
        return False

    host = urlparse(url).netloc.lower().strip()
    if host.startswith('www.'):
        host = host[4:]
    if not host:
        return False

    return any(host == domain or host.endswith(f'.{domain}') for domain in domains)
