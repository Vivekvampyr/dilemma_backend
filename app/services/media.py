import uuid
import os
from pathlib import Path
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.media import PostMedia, MediaType

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}


async def upload_post_media(
    db: AsyncSession,
    post_id: uuid.UUID,
    files: list[UploadFile],
) -> list[PostMedia]:
    if len(files) > settings.MAX_IMAGES_PER_POST:
        raise HTTPException(
            status_code=400,
            detail=f"Max {settings.MAX_IMAGES_PER_POST} files per post",
        )

    media_records = []

    for idx, file in enumerate(files):
        content_type = file.content_type or ""

        if content_type in ALLOWED_IMAGE_TYPES:
            media_type = MediaType.image
            max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
        elif content_type in ALLOWED_VIDEO_TYPES:
            media_type = MediaType.video
            max_bytes = settings.MAX_VIDEO_SIZE_MB * 1024 * 1024
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {content_type}")

        data = await file.read()

        if len(data) > max_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"{file.filename} exceeds size limit",
            )

        if settings.MEDIA_STORAGE == "s3":
            url, key = await _upload_to_s3(data, content_type, post_id)
        else:
            url, key = await _save_locally(data, content_type, post_id)

        record = PostMedia(
            post_id=post_id,
            media_type=media_type,
            url=url,
            storage_key=key,
            original_filename=file.filename,
            file_size_bytes=len(data),
            mime_type=content_type,
            display_order=idx,
        )
        db.add(record)
        media_records.append(record)

    await db.flush()
    return media_records


async def _save_locally(data: bytes, content_type: str, post_id: uuid.UUID):
    ext = content_type.split("/")[-1]
    filename = f"{post_id}_{uuid.uuid4().hex}.{ext}"
    filepath = Path(settings.UPLOAD_DIR) / filename
    filepath.write_bytes(data)
    url = f"/media/{filename}"
    return url, str(filepath)


async def _upload_to_s3(data: bytes, content_type: str, post_id: uuid.UUID):
    import boto3
    ext = content_type.split("/")[-1]
    key = f"posts/{post_id}/{uuid.uuid4().hex}.{ext}"
    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )
    s3.put_object(Bucket=settings.S3_BUCKET_NAME, Key=key, Body=data, ContentType=content_type)
    url = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
    return url, key