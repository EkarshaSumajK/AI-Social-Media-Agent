from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re
from typing import Any

import yaml

from app.core.config import get_settings

settings = get_settings()


class _PromptDict(dict[str, Any]):
    def __missing__(self, key: str) -> str:
        return '{' + key + '}'


class PromptCatalog:
    def __init__(self, prompts_root: Path | None = None) -> None:
        self.prompts_root = prompts_root or Path(settings.prompts_dir)
        self._cache: dict[str, dict[str, Any]] = {}

    def get_prompt(self, *, bundle: str, key: str, context: dict[str, Any] | None = None) -> tuple[str, str]:
        payload = self._load_bundle(bundle)
        block = payload.get(key)
        if not isinstance(block, dict):
            raise KeyError(f'Prompt key "{key}" not found in bundle "{bundle}"')

        system_template = str(block.get('system', '')).strip()
        user_template = str(block.get('user', '')).strip()
        rendered_context = _PromptDict({k: _stringify(v) for k, v in (context or {}).items()})
        return _render_template(system_template, rendered_context), _render_template(user_template, rendered_context)

    def _load_bundle(self, bundle: str) -> dict[str, Any]:
        if bundle in self._cache:
            return self._cache[bundle]

        path = self.prompts_root / bundle
        if not path.exists():
            raise FileNotFoundError(f'Prompt bundle not found: {path}')
        with path.open('r', encoding='utf-8') as handle:
            data = yaml.safe_load(handle) or {}
        if not isinstance(data, dict):
            raise ValueError(f'Prompt bundle must be a mapping: {path}')
        self._cache[bundle] = data
        return data


def _stringify(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return ', '.join(str(item) for item in value)
    return str(value)


def _render_template(template: str, values: dict[str, Any]) -> str:
    pattern = re.compile(r'\{([a-zA-Z0-9_]+)\}')

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return str(values.get(key, match.group(0)))

    return pattern.sub(replace, template)


@lru_cache(maxsize=1)
def get_prompt_catalog() -> PromptCatalog:
    return PromptCatalog()
