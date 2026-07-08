"""On-demand translation with bot protection.

Real user view → translate batch → save to DB (columns name_en/ru/uk, text_en/ru/uk).
Bot traffic → return empty, never translate.
"""
import json
import re
import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

_client: OpenAI | None = None

BOT_RE = re.compile(
    r'bot\b|crawler|spider|scraper|\bwget\b|curl/[0-9]|python-requests|python-urllib|'
    r'java/[0-9]|go-http-client|googlebot|bingbot|slurp|duckduckbot|baiduspider|'
    r'yandexbot|semrushbot|ahrefsbot|mozbot|rogerbot|facebot|ia_archiver|linkedinbot|'
    r'twitterbot|telegrambot|discordbot|applebot|dotbot|exabot|gigabot|'
    r'uptimerobot|pingdom|dataprovider|archive\.org_bot|commoncrawl|'
    r'headlesschrome|phantomjs|selenium|puppeteer|playwright|'
    r'prerender|lighthouse',
    re.IGNORECASE,
)

LANG_NAMES: dict[str, str] = {
    "en": "English",
    "ru": "Russian",
    "uk": "Ukrainian",
}


def is_bot(user_agent: str | None) -> bool:
    if not user_agent or len(user_agent) < 10:
        return True
    return bool(BOT_RE.search(user_agent))


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not configured")
        _client = OpenAI(api_key=api_key)
    return _client


def _extract_array(text: str) -> list | None:
    """Pull first JSON array out of a response string."""
    m = re.search(r'\[.*?\]', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except Exception:
            pass
    # Maybe the whole response is valid JSON array
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
        # {"items": [...]} or {"translations": [...]}
        if isinstance(parsed, dict):
            for v in parsed.values():
                if isinstance(v, list):
                    return v
    except Exception:
        pass
    return None


def translate_batch(texts: list[str], target_lang: str) -> list[str]:
    """Translate a list of texts to target_lang using GPT-4o-mini.

    Returns same-length list. Falls back to originals on any error.
    """
    if not texts:
        return []
    lang_name = LANG_NAMES.get(target_lang, "English")
    client = _get_client()

    prompt = (
        f"Translate each item from Greek or English to {lang_name}. "
        "Return ONLY a JSON array of translated strings in the exact same order. "
        "Keep proper nouns, brand names, and numbers unchanged.\n"
        f"Input: {json.dumps(texts, ensure_ascii=False)}"
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=4096,
        )
        raw = resp.choices[0].message.content or ""
        result = _extract_array(raw)
        if result and len(result) == len(texts):
            return [str(r) for r in result]
        logger.warning("Translation returned wrong count: %d vs %d", len(result or []), len(texts))
    except Exception as exc:
        logger.warning("Translation failed: %s", exc)
    return texts
