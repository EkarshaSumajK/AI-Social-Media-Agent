from __future__ import annotations

import base64
import hashlib
import logging
import re
import time

import httpx
from openai import AsyncOpenAI

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# gpt-image-1 supported sizes: 1024x1024, 1024x1536, 1536x1024, auto
_ARTICLE_BODY_CONFIG = {
    'size': '1536x1024',
    'layout': (
        'Design a comprehensive, long-form INFOGRAPHIC summarizing an article in landscape (3:2) format.\n'
        'Layout structure:\n'
        '- Top: Full-width headline banner with the article title in large bold font\n'
        '- Body: 5-6 content cards arranged in a 2-column grid, each with a mini headline '
        'and 2-3 bullet points extracted from the article sections\n'
        '- Bottom: Key takeaway callout box with a strong stat or quote + clinic branding bar\n'
        'Visual style: Professional health publication aesthetic. Clean layout with generous whitespace. '
        'Use a calming color palette (deep teal primary, soft blue accents, warm amber highlights). '
        'Sans-serif typography with strong hierarchy. Rounded card corners, subtle shadows. '
        'Each content card should have a colored left border or icon to distinguish sections. '
        'Should feel like a well-designed one-page summary someone could share or print.'
    ),
}

PLATFORM_CONFIG: dict[str, dict] = {
    'article-body': _ARTICLE_BODY_CONFIG,
    'article_body': _ARTICLE_BODY_CONFIG,
    'instagram': {
        'size': '1024x1024',
        'layout': (
            'Design a bold, scroll-stopping INFOGRAPHIC for Instagram in square (1:1) format.\n'
            'Layout structure:\n'
            '- Top: A short, punchy headline in large bold font (max 8 words)\n'
            '- Middle: 3-4 key points or stats as icon + short text pairs arranged vertically\n'
            '- Bottom: Clinic name/branding bar with a subtle call-to-action\n'
            'Visual style: Vibrant but professional. Use bold colors (deep teal, coral, warm gold) '
            'with clean sans-serif typography. Use flat icons or simple illustrations next to each point. '
            'High contrast for readability on mobile. Modern health/wellness infographic aesthetic.'
        ),
    },
    'linkedin': {
        'size': '1536x1024',
        'layout': (
            'Design a professional, data-driven INFOGRAPHIC for LinkedIn in landscape (3:2) format.\n'
            'Layout structure:\n'
            '- Left side: Bold headline + a key statistic in large font\n'
            '- Right side: 3-4 bullet points with small icons, cleanly spaced\n'
            '- Bottom strip: Clinic branding + a professional call-to-action\n'
            'Visual style: Corporate yet warm. Use muted blues, soft grays, and one accent color. '
            'Clean sans-serif fonts, plenty of whitespace. Minimal flat icons. '
            'Should look like a professional health organization would publish it.'
        ),
    },
    'twitter': {
        'size': '1536x1024',
        'layout': (
            'Design a high-impact, shareable INFOGRAPHIC for Twitter/X in landscape (3:2) format.\n'
            'Layout structure:\n'
            '- Top-left: Bold headline in large font (max 6 words) that grabs attention\n'
            '- Center: 1 big stat or fact in oversized typography as the focal point\n'
            '- Below: 2-3 supporting points in smaller text with simple dividers\n'
            '- Bottom: Thin branding bar with clinic name\n'
            'Visual style: High-contrast, bold. Dark background with bright accent colors '
            '(teal, amber, white text). Strong typography hierarchy. '
            'Designed to stop the scroll — think "breaking info" visual energy.'
        ),
    },
    'facebook': {
        'size': '1536x1024',
        'layout': (
            'Design a warm, community-friendly INFOGRAPHIC for Facebook in landscape (3:2) format.\n'
            'Layout structure:\n'
            '- Top: Warm headline in friendly bold font\n'
            '- Middle: Content organized as a numbered list or tip cards (3-5 items) '
            'with small illustrative icons next to each\n'
            '- Bottom: Clinic branding + "Learn more" style call-to-action\n'
            'Visual style: Warm and inviting. Soft oranges, calming blues, gentle greens. '
            'Rounded shapes, friendly typography. Should feel approachable and shareable — '
            'like something a parent would share with other parents.'
        ),
    },
}


def _extract_key_points(caption: str, article_summary: str) -> str:
    """Pull out the most infographic-worthy content from the caption and article."""
    all_text = f"{caption}\n{article_summary}"

    # Extract any statistics or numbers
    stats = re.findall(r'[^.]*?\d+[^.]*\.', all_text)
    stats_text = '\n'.join(f'- {s.strip()}' for s in stats[:3]) if stats else ''

    # Extract sentences that look like tips or action items
    tips = re.findall(r'[^.]*?(?:should|can|try|help|encourage|create|set|monitor|talk)[^.]*\.', all_text, re.IGNORECASE)
    tips_text = '\n'.join(f'- {t.strip()}' for t in tips[:4]) if tips else ''

    parts = []
    if stats_text:
        parts.append(f'Key statistics:\n{stats_text}')
    if tips_text:
        parts.append(f'Key tips/actions:\n{tips_text}')
    if not parts:
        # Fallback: use first 3 sentences
        sentences = [s.strip() for s in re.split(r'[.!?]+', all_text) if s.strip()]
        parts.append('\n'.join(f'- {s}' for s in sentences[:4]))

    return '\n'.join(parts)


class ImageService:
    def __init__(self) -> None:
        if not settings.llm_api_key:
            raise RuntimeError('OpenAI API key (LLM_API_KEY) is not configured.')
        self.client = AsyncOpenAI(api_key=settings.llm_api_key)

    def build_prompt(
        self,
        platform: str,
        caption: str,
        article_title: str,
        article_summary: str = '',
    ) -> str:
        config = PLATFORM_CONFIG.get(platform)
        if not config:
            raise ValueError(f'Unsupported platform: {platform}')

        clinic_name = settings.clinic_name
        key_points = _extract_key_points(caption, article_summary)

        return (
            f"{config['layout']}\n\n"
            f"CONTENT FOR THIS INFOGRAPHIC:\n"
            f"Topic/Headline: {article_title}\n"
            f"Caption context: {caption}\n\n"
            f"Key points to feature in the infographic:\n{key_points}\n\n"
            f"Branding: {clinic_name}\n\n"
            "CRITICAL RULES:\n"
            "- This MUST be an INFOGRAPHIC — not a photo, not an abstract background.\n"
            "- Include actual readable TEXT in the image: headline, key points, stats, tips.\n"
            "- All text must be spelled correctly and clearly legible.\n"
            "- Use icons, dividers, and visual hierarchy to organize the information.\n"
            "- Do NOT use photorealistic human faces or children.\n"
            "- Use flat illustrations, icons, or abstract people silhouettes if needed.\n"
            "- The infographic should be self-contained — someone should understand the core message "
            "just by looking at the image without reading the caption.\n"
            "- Keep text concise: short headlines, bullet points, not paragraphs.\n"
            "- Ensure strong color contrast for text readability.\n"
            "- Include the clinic name in a subtle branding bar."
        )

    async def generate_image(
        self,
        platform: str,
        caption: str,
        article_title: str,
        article_summary: str = '',
    ) -> bytes:
        config = PLATFORM_CONFIG.get(platform.lower())
        if not config:
            raise ValueError(f'Unsupported platform: {platform}')

        prompt = self.build_prompt(platform, caption, article_title, article_summary)

        response = await self.client.images.generate(
            model='gpt-image-1',
            prompt=prompt,
            size=config['size'],
            n=1,
        )

        image_b64 = response.data[0].b64_json
        if not image_b64:
            raise RuntimeError('OpenAI returned no image data.')

        return base64.b64decode(image_b64)

    async def upload_to_cloudinary(self, image_bytes: bytes, platform: str) -> str:
        if not settings.cloudinary_cloud_name or not settings.cloudinary_api_key or not settings.cloudinary_api_secret:
            raise RuntimeError('Cloudinary is not configured.')

        b64_data = base64.b64encode(image_bytes).decode('utf-8')
        data_url = f'data:image/png;base64,{b64_data}'

        timestamp = int(time.time())
        folder = 'ai-social-images'

        params_to_sign = f'folder={folder}&timestamp={timestamp}'
        signature = hashlib.sha1(
            f'{params_to_sign}{settings.cloudinary_api_secret}'.encode()
        ).hexdigest()

        upload_url = f'https://api.cloudinary.com/v1_1/{settings.cloudinary_cloud_name}/image/upload'

        form_data = {
            'file': data_url,
            'api_key': settings.cloudinary_api_key,
            'timestamp': str(timestamp),
            'folder': folder,
            'signature': signature,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(upload_url, data=form_data)
            resp.raise_for_status()
            body = resp.json()

        return body['secure_url']

    async def generate_and_upload(
        self,
        platform: str,
        caption: str,
        article_title: str,
        article_summary: str = '',
    ) -> str:
        logger.info('Generating infographic for platform=%s, article=%s', platform, article_title[:60])
        image_bytes = await self.generate_image(platform, caption, article_title, article_summary)
        url = await self.upload_to_cloudinary(image_bytes, platform)
        logger.info('Infographic uploaded to Cloudinary: %s', url)
        return url
