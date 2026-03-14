import base64
import hashlib
import time

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_reviewer
from app.core.config import get_settings
from app.models.user import User

router = APIRouter()
settings = get_settings()


class ImageUploadRequest(BaseModel):
    image_data: str  # base64 data URL: "data:image/png;base64,..."


class ImageUploadResponse(BaseModel):
    url: str
    public_id: str


@router.post('/upload', response_model=ImageUploadResponse)
async def upload_image(
    payload: ImageUploadRequest,
    current_user: User = Depends(get_current_reviewer),
) -> ImageUploadResponse:
    """Upload a base64 image to Cloudinary and return the hosted URL."""
    if not settings.cloudinary_cloud_name or not settings.cloudinary_api_key or not settings.cloudinary_api_secret:
        raise HTTPException(status_code=500, detail='Cloudinary is not configured. Add CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET to .env')

    # Build signed upload params
    timestamp = int(time.time())
    folder = 'social-infographics'

    params_to_sign = f'folder={folder}&timestamp={timestamp}'
    signature = hashlib.sha1(f'{params_to_sign}{settings.cloudinary_api_secret}'.encode()).hexdigest()

    upload_url = f'https://api.cloudinary.com/v1_1/{settings.cloudinary_cloud_name}/image/upload'

    form_data = {
        'file': payload.image_data,
        'api_key': settings.cloudinary_api_key,
        'timestamp': str(timestamp),
        'folder': folder,
        'signature': signature,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(upload_url, data=form_data)
            resp.raise_for_status()
            body = resp.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f'Cloudinary upload failed: {exc.response.text}') from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f'Image upload error: {exc}') from exc

    return ImageUploadResponse(url=body['secure_url'], public_id=body['public_id'])
