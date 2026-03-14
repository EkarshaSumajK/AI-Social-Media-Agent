from __future__ import annotations

from datetime import datetime, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.article import Article
from app.models.social_post import SocialPost

settings = get_settings()


class SocialPublisher:
    async def publish_pending_posts(self, db: AsyncSession, article: Article) -> dict[str, str]:
        if article.status != 'published':
            raise RuntimeError('Social publishing is allowed only after article is published.')

        outcomes: dict[str, str] = {}
        for post in article.social_posts:
            if post.status == 'posted':
                outcomes[post.platform] = 'already_posted'
                continue
            if post.status != 'ready':
                outcomes[post.platform] = 'skipped_not_ready'
                continue

            caption = (post.edited_caption or post.caption).strip()
            try:
                external_id = await self._dispatch(platform=post.platform, caption=caption, link=article.published_url)
                post.status = 'posted'
                post.external_post_id = external_id
                post.error_message = None
                post.posted_at = datetime.now(timezone.utc)
                outcomes[post.platform] = 'posted'
            except Exception as exc:  # noqa: BLE001
                post.status = 'failed'
                post.error_message = str(exc)
                outcomes[post.platform] = 'failed'

            db.add(post)

        await db.flush()
        return outcomes

    async def _dispatch(self, *, platform: str, caption: str, link: str | None, image_url: str | None = None) -> str:
        if platform == 'facebook':
            return await self._post_facebook(caption, link, image_url)
        if platform == 'instagram':
            return await self._post_instagram(caption, image_url)
        if platform == 'linkedin':
            return await self._post_linkedin(caption, link)
        if platform == 'twitter':
            return await self._post_x(caption, link)
        raise RuntimeError(f'Unsupported platform: {platform}')

    async def _post_facebook(self, caption: str, link: str | None, image_url: str | None = None) -> str:
        if not settings.meta_access_token or not settings.facebook_page_id:
            raise RuntimeError('Facebook settings are missing')

        if image_url:
            # Post as photo with caption
            endpoint = f'https://graph.facebook.com/v20.0/{settings.facebook_page_id}/photos'
            payload = {'caption': caption, 'url': image_url, 'access_token': settings.meta_access_token}
        else:
            endpoint = f'https://graph.facebook.com/v20.0/{settings.facebook_page_id}/feed'
            payload = {'message': caption, 'access_token': settings.meta_access_token}
            if link:
                payload['link'] = link

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(endpoint, data=payload)
            response.raise_for_status()
            body = response.json()

        return str(body.get('id', ''))

    async def _post_instagram(self, caption: str, image_url: str | None = None) -> str:
        if not settings.meta_access_token or not settings.instagram_business_id:
            raise RuntimeError('Instagram settings are missing')

        resolved_image_url = image_url or settings.instagram_image_url
        if not resolved_image_url:
            raise RuntimeError('An image URL is required for Instagram publishing. Generate an image and upload it first.')

        create_url = f'https://graph.facebook.com/v20.0/{settings.instagram_business_id}/media'
        publish_url = f'https://graph.facebook.com/v20.0/{settings.instagram_business_id}/media_publish'

        async with httpx.AsyncClient(timeout=20.0) as client:
            create_resp = await client.post(
                create_url,
                data={
                    'image_url': resolved_image_url,
                    'caption': caption,
                    'access_token': settings.meta_access_token,
                },
            )
            create_resp.raise_for_status()
            creation_id = create_resp.json().get('id')
            if not creation_id:
                raise RuntimeError('Instagram media creation failed')

            publish_resp = await client.post(
                publish_url,
                data={
                    'creation_id': creation_id,
                    'access_token': settings.meta_access_token,
                },
            )
            publish_resp.raise_for_status()
            body = publish_resp.json()

        return str(body.get('id', creation_id))

    async def _post_linkedin(self, caption: str, link: str | None) -> str:
        if not settings.linkedin_access_token or not settings.linkedin_organization_id:
            raise RuntimeError('LinkedIn settings are missing')

        endpoint = 'https://api.linkedin.com/v2/ugcPosts'
        urn = f'urn:li:organization:{settings.linkedin_organization_id}'
        payload = {
            'author': urn,
            'lifecycleState': 'PUBLISHED',
            'specificContent': {
                'com.linkedin.ugc.ShareContent': {
                    'shareCommentary': {'text': f'{caption}\n{link or ""}'.strip()},
                    'shareMediaCategory': 'NONE',
                }
            },
            'visibility': {'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'},
        }

        headers = {
            'Authorization': f'Bearer {settings.linkedin_access_token}',
            'X-Restli-Protocol-Version': '2.0.0',
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
        return response.headers.get('x-restli-id', 'linkedin-posted')

    async def _post_x(self, caption: str, link: str | None) -> str:
        if not settings.x_bearer_token:
            raise RuntimeError('X token is missing')

        endpoint = 'https://api.x.com/2/tweets'
        text = f'{caption}\n{link or ""}'.strip()
        headers = {'Authorization': f'Bearer {settings.x_bearer_token}'}

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(endpoint, json={'text': text[:280]}, headers=headers)
            response.raise_for_status()
            body = response.json()
        return str((body.get('data') or {}).get('id', ''))


def mark_posts_ready(article: Article) -> None:
    for post in article.social_posts:
        if post.status == 'draft':
            post.status = 'ready'


def upsert_social_posts(article: Article, posts_by_platform: dict[str, str]) -> None:
    by_platform = {post.platform: post for post in article.social_posts}
    for platform_name, caption in posts_by_platform.items():
        existing = by_platform.get(platform_name)
        if existing:
            existing.caption = caption
            existing.status = 'draft'
            continue

        article.social_posts.append(
            SocialPost(
                platform=platform_name,
                caption=caption,
                status='draft',
            )
        )
