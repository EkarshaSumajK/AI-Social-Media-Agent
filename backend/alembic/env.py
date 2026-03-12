from __future__ import annotations

from logging.config import fileConfig
from pathlib import Path
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from alembic import context
from sqlalchemy import engine_from_config, pool, text as sa_text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / 'backend'
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.core.database import Base  # noqa: E402
import app.models  # noqa: F401,E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _sync_database_url() -> str:
    url = get_settings().database_url_dashboard
    if '+asyncpg' in url:
        url = url.replace('+asyncpg', '+psycopg')

    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))

    # Normalize async URL patterns for psycopg migrations.
    ssl_value = query.pop('ssl', None)
    if ssl_value and 'sslmode' not in query:
        normalized = ssl_value.strip().lower()
        if normalized in {'1', 'true', 'yes', 'on'}:
            query['sslmode'] = 'require'
        elif normalized in {'0', 'false', 'no', 'off'}:
            query['sslmode'] = 'disable'
        else:
            query['sslmode'] = ssl_value

    # Drop asyncpg-specific parameters that psycopg doesn't understand.
    query.pop('prepared_statement_cache_size', None)
    query.pop('statement_cache_size', None)

    rebuilt = parts._replace(query=urlencode(query))
    return urlunsplit(rebuilt)


config.set_main_option('sqlalchemy.url', _sync_database_url())
target_metadata = Base.metadata

_schema = get_settings().database_schema


def run_migrations_offline() -> None:
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        compare_type=True,
        version_table_schema=_schema,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Create the target schema if it doesn't exist yet.
        connection.execute(sa_text(f'CREATE SCHEMA IF NOT EXISTS {_schema}'))
        connection.execute(sa_text(f'SET search_path TO {_schema}, public'))
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            version_table_schema=_schema,
            include_schemas=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
