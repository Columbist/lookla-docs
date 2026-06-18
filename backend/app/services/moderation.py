import httpx
from app.core.config import get_settings

settings = get_settings()

# Partial list — full list loaded from file or package
DISPOSABLE_DOMAINS = {
    "mailinator.com", "tempmail.com", "10minutemail.com", "guerrillamail.com",
    "throwam.com", "yopmail.com", "sharklasers.com", "guerrillamailblock.com",
    "grr.la", "guerrillamail.info", "spam4.me", "trashmail.com", "trashmail.me",
    "dispostable.com", "spamgourmet.com", "spamgourmet.net", "mailnull.com",
    "maildrop.cc", "fakeinbox.com", "tempinbox.com", "getairmail.com",
}


def is_disposable_email(email: str) -> bool:
    domain = email.split("@")[-1].lower()
    return domain in DISPOSABLE_DOMAINS


async def check_text(text: str) -> dict:
    """OpenAI Moderation API — free, no limits in practice."""
    if not settings.openai_api_key or not text:
        return {"flagged": False}
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                "https://api.openai.com/v1/moderations",
                json={"input": text},
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                timeout=10,
            )
            if r.status_code == 200:
                result = r.json()["results"][0]
                return {
                    "flagged": result["flagged"],
                    "scores": result["category_scores"],
                }
    except Exception as e:
        print(f"[moderation] text check error: {e}")
    return {"flagged": False}


async def check_image(image_url: str) -> dict:
    """Google Cloud Vision Safe Search — 1000 req/month free."""
    if not settings.google_vision_api_key or not image_url:
        return {"flagged": False}
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"https://vision.googleapis.com/v1/images:annotate?key={settings.google_vision_api_key}",
                json={"requests": [{"image": {"source": {"imageUri": image_url}}, "features": [{"type": "SAFE_SEARCH_DETECTION"}]}]},
                timeout=15,
            )
            if r.status_code == 200:
                ss = r.json()["responses"][0].get("safeSearchAnnotation", {})
                flagged = any(ss.get(k) in ("LIKELY", "VERY_LIKELY") for k in ("adult", "violence", "racy"))
                return {"flagged": flagged, "labels": ss}
    except Exception as e:
        print(f"[moderation] image check error: {e}")
    return {"flagged": False}
