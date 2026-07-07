"""Cloudflare R2 upload helpers (S3-compatible via boto3)."""
import hashlib
import logging
import boto3
from botocore.config import Config as BotoConfig

log = logging.getLogger(__name__)

_client = None


def get_r2_client(settings):
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=settings.r2_endpoint,
            aws_access_key_id=settings.r2_access_key,
            aws_secret_access_key=settings.r2_secret_key,
            config=BotoConfig(signature_version="s3v4"),
            region_name="auto",
        )
    return _client


def upload_bytes(settings, data: bytes, key: str, content_type: str = "image/jpeg") -> str:
    client = get_r2_client(settings)
    client.put_object(
        Bucket=settings.r2_bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
        CacheControl="public, max-age=31536000",
    )
    return f"{settings.r2_cdn_url}/{key}"


def r2_key_for_photo(salon_id: int, photo_id: int, source_url: str, ext: str = "jpg") -> str:
    url_hash = hashlib.md5(source_url.encode()).hexdigest()[:12]
    return f"photos/{salon_id}/{url_hash}.{ext}"
