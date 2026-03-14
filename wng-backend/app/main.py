from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import verify_schema_ready
from app.services.user_service import ensure_admin_user

settings = get_settings()

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        integrations=[FastApiIntegration()],
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    await verify_schema_ready()
    await ensure_admin_user()
    yield


app = FastAPI(title=settings.project_name, lifespan=lifespan)

# Configure CORS - allow frontend and localhost
allowed_origins = [
    settings.frontend_url,
    'http://localhost:3000',
    'https://ai-social-media-agent-one.vercel.app',  # Your Vercel domain
]

# Remove None values and add wildcard for development
allowed_origins = [origin for origin in allowed_origins if origin]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
    expose_headers=['*'],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get('/', tags=['system'])
async def root() -> dict[str, str]:
    return {'status': 'ok', 'service': settings.project_name}
