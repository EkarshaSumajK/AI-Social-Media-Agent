from collections.abc import AsyncGenerator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings

settings = get_settings()

_schema = settings.database_schema


class SchemaAwareSession(AsyncSession):
    """Custom session that sets search_path on transaction begin."""
    
    async def begin(self, nested: bool = False):
        trans = await super().begin(nested=nested)
        if not nested:
            await self.execute(text(f"SET search_path TO {_schema}, public"))
        return trans


def _async_database_url() -> str:
    url = settings.database_url_dashboard
    if '+psycopg' in url:
        url = url.replace('+psycopg', '+asyncpg')

    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))

    # asyncpg expects "ssl", while many providers/docs use "sslmode".
    sslmode = query.pop('sslmode', None)
    if sslmode and 'ssl' not in query:
        normalized = sslmode.strip().lower()
        if normalized in {'disable', 'allow', 'prefer'}:
            query['ssl'] = 'false'
        else:
            query['ssl'] = 'require'

    # libpq-specific options are not accepted by asyncpg kwargs.
    query.pop('channel_binding', None)
    query.pop('gssencmode', None)
    query.pop('target_session_attrs', None)

    rebuilt = parts._replace(query=urlencode(query))
    return urlunsplit(rebuilt)


engine = create_async_engine(
    _async_database_url(),
    echo=False,
    pool_pre_ping=True,
)
SessionLocal = async_sessionmaker(engine, class_=SchemaAwareSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        # Ensure search_path is set even without explicit transaction
        await session.execute(text(f"SET search_path TO {_schema}, public"))
        yield session


async def verify_schema_ready() -> None:
    """
    Verify that Alembic-managed schema exists before serving requests.
    """
    async with SessionLocal() as session:
        # Set search_path for schema isolation
        await session.execute(text(f"SET search_path TO {_schema}, public"))
        try:
            await session.execute(text('SELECT version_num FROM alembic_version LIMIT 1'))
        except SQLAlchemyError as exc:
            raise RuntimeError(
                'Database schema is not ready. Run `alembic upgrade head` before starting the API.'
            ) from exc
