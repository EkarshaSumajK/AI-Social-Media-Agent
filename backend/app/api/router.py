from fastapi import APIRouter

from app.api.routes import (
    audience_content,
    audit,
    auth,
    campaigns,
    competitors,
    daily_posts,
    drafts,
    health,
    hooks,
    image_text,
    images,
    paraphraser,
    performance,
    platform_content,
    published,
    regional,
    repurpose,
    scheduling,
    scoring,
    social_accounts,
    swipe_files,
    thought_leadership,
    topics,
    youtube_shorts,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=['health'])
api_router.include_router(image_text.router, prefix='/image-text', tags=['image-text'])
api_router.include_router(images.router, prefix='/images', tags=['images'])
api_router.include_router(auth.router, prefix='/auth', tags=['auth'])
api_router.include_router(topics.router, prefix='/topics', tags=['topics'])
api_router.include_router(drafts.router, prefix='/drafts', tags=['drafts'])
api_router.include_router(audit.router, prefix='/audit', tags=['audit'])
api_router.include_router(published.router, prefix='/published', tags=['published'])
api_router.include_router(paraphraser.router, prefix='/paraphrase', tags=['paraphrase'])
api_router.include_router(scoring.router, prefix='/scoring', tags=['scoring'])
api_router.include_router(daily_posts.router, prefix='/daily-posts', tags=['daily-posts'])
api_router.include_router(repurpose.router, prefix='/repurpose', tags=['repurpose'])
api_router.include_router(platform_content.router, prefix='/platform-content', tags=['platform-content'])
api_router.include_router(thought_leadership.router, prefix='/thought-leadership', tags=['thought-leadership'])
api_router.include_router(audience_content.router, prefix='/audience-content', tags=['audience-content'])
api_router.include_router(campaigns.router, prefix='/campaigns', tags=['campaigns'])
api_router.include_router(competitors.router, prefix='/competitors', tags=['competitors'])
api_router.include_router(hooks.router, prefix='/hooks', tags=['hooks'])
api_router.include_router(swipe_files.router, prefix='/swipe-files', tags=['swipe-files'])
api_router.include_router(performance.router, prefix='/performance', tags=['performance'])
api_router.include_router(youtube_shorts.router, prefix='/youtube-shorts', tags=['youtube-shorts'])
api_router.include_router(scheduling.router, prefix='/scheduling', tags=['scheduling'])
api_router.include_router(social_accounts.router, prefix='/social-accounts', tags=['social-accounts'])
api_router.include_router(regional.router, prefix='/regional', tags=['regional'])
