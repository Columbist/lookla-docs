"""
Migrate primary salon photos from Google Places API URLs to Cloudflare R2.

Fetches only photos where:
  - url LIKE '%places.googleapis.com%'  (not yet in R2)
  - is_primary = true                   (main photo, shown in cards)

Each photo: GET google url (follow redirect) → upload to R2 → update DB.
Cost: ~$0.007/photo (Google Places Photo API) × ~4654 = ~$33 one-time.
After migration: served from cdn.lookla.gr, no more Google API costs per view.
"""
import os
import time
import hashlib
import logging
import psycopg2
import httpx
import boto3
from botocore.config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger(__name__)

DB_DSN = f"host=localhost port=5432 dbname=beauty_gr user=beauty password=changeme_strong_password"

R2_ENDPOINT  = os.environ.get("R2_ENDPOINT",  "https://74bc94f3db8c7bac9a1e983dded06735.r2.cloudflarestorage.com")
R2_ACCESS    = os.environ.get("R2_ACCESS_KEY", "0730da8d9cb6451935599462f3965bd2")
R2_SECRET    = os.environ.get("R2_SECRET_KEY", "87821c3f762e66bbdb94a0c3e1771a4ea2b8a8aa0902cb912d9951dc185d0692")
R2_BUCKET    = os.environ.get("R2_BUCKET",     "lookla-photos")
CDN_URL      = os.environ.get("R2_CDN_URL",    "https://cdn.lookla.gr")

s3 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS,
    aws_secret_access_key=R2_SECRET,
    config=Config(signature_version="s3v4"),
    region_name="auto",
)


def fetch_photo(url: str) -> tuple[bytes, str] | None:
    """Follow Google Places photo redirect, return (bytes, content_type)."""
    try:
        r = httpx.get(url, follow_redirects=True, timeout=20)
        r.raise_for_status()
        ct = r.headers.get("content-type", "image/jpeg").split(";")[0].strip()
        return r.content, ct
    except Exception as e:
        log.warning("Fetch failed %s: %s", url[:80], e)
        return None


def upload_to_r2(data: bytes, key: str, content_type: str) -> str:
    s3.put_object(
        Bucket=R2_BUCKET,
        Key=key,
        Body=data,
        ContentType=content_type,
        CacheControl="public, max-age=31536000",
    )
    return f"{CDN_URL}/{key}"


def run():
    conn = psycopg2.connect(DB_DSN)
    cur  = conn.cursor()

    cur.execute("""
        SELECT p.id, p.salon_id, p.url
        FROM photos p
        WHERE p.url LIKE '%places.googleapis.com%'
          AND p.is_primary = true
        ORDER BY p.salon_id
    """)
    rows = cur.fetchall()
    log.info("Photos to migrate: %d", len(rows))

    ok = fail = skip = 0

    for photo_id, salon_id, url in rows:
        result = fetch_photo(url)
        if result is None:
            fail += 1
            time.sleep(0.5)
            continue

        data, content_type = result
        if len(data) < 1000:
            log.warning("Skipping tiny response for photo %d (%d bytes)", photo_id, len(data))
            skip += 1
            continue

        ext = "jpg" if "jpeg" in content_type else content_type.split("/")[-1]
        key = f"photos/{salon_id}/{hashlib.md5(url.encode()).hexdigest()[:12]}.{ext}"

        try:
            cdn_url = upload_to_r2(data, key, content_type)
            cur.execute("UPDATE photos SET url = %s WHERE id = %s", (cdn_url, photo_id))
            conn.commit()
            ok += 1
            if ok % 50 == 0:
                log.info("Progress: %d ok / %d fail / %d skip (of %d)", ok, fail, skip, len(rows))
        except Exception as e:
            log.error("R2 upload failed for photo %d: %s", photo_id, e)
            conn.rollback()
            fail += 1

        time.sleep(0.15)

    cur.close()
    conn.close()
    log.info("Done: %d migrated, %d failed, %d skipped", ok, fail, skip)


if __name__ == "__main__":
    run()
