"""
Auto-generate salon descriptions via Claude Haiku API.

Cost estimate: ~$8-10 for all 6126 salons without descriptions
  - Input:  ~1.5M tokens × $0.80/M = $1.20
  - Output: ~1.8M tokens × $4.00/M = $7.20

Usage:
  python3 generate_descriptions.py [--limit N] [--dry-run]

Auth priority:
  1. ANTHROPIC_API_KEY env var (api key)
  2. ANTHROPIC_AUTH_TOKEN env var (oauth bearer)
  3. ~/.claude/.credentials.json (claude code oauth, auto-detected)

Generates el + en descriptions in one call per salon.
Saves to salons.description_el and salons.description.
"""
import os
import sys
import time
import logging
import argparse
import json

import anthropic
import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://beauty:changeme_strong_password@localhost:5432/beauty_gr",
)

CREDS_FILE = os.path.expanduser("~/.claude/.credentials.json")


_current_token: str | None = None
_client: anthropic.Anthropic | None = None


def get_anthropic_client() -> anthropic.Anthropic | None:
    """Returns an Anthropic client, re-reading credentials file each call to handle token refresh."""
    global _current_token, _client

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        if _client is None:
            logger.info("Using ANTHROPIC_API_KEY")
            _client = anthropic.Anthropic(api_key=api_key)
        return _client

    auth_token = os.getenv("ANTHROPIC_AUTH_TOKEN")
    if auth_token:
        if _client is None:
            logger.info("Using ANTHROPIC_AUTH_TOKEN")
            _client = anthropic.Anthropic(auth_token=auth_token)
        return _client

    # Re-read credentials file every call — Claude Code may refresh the token
    if os.path.exists(CREDS_FILE):
        with open(CREDS_FILE) as f:
            creds = json.load(f)
        token = creds.get("claudeAiOauth", {}).get("accessToken")
        if token and token != _current_token:
            logger.info("(Re)loading Claude Code OAuth token from %s", CREDS_FILE)
            _current_token = token
            _client = anthropic.Anthropic(auth_token=token)
        return _client

    return None

SYSTEM_PROMPT = """You write short descriptions for beauty salons listed on Lookla.gr, a Greek beauty marketplace.

Rules:
- Write TWO descriptions: one in Greek (el), one in English (en)
- Each description: 2-3 sentences, 50-80 words
- Tone: warm, professional, inviting
- Use only the provided facts. Never invent services, awards, or claims
- If rating is high (≥4.5), mention it naturally
- If services are listed, mention 2-3 of them
- Do NOT mention "Lookla" or "Google" or "Treatwell"
- Output ONLY valid JSON: {"el": "...", "en": "..."}"""

def build_prompt(salon: dict, services: list[str]) -> str:
    parts = [f"Salon name: {salon['name']}"]
    if salon.get("address_city"):
        parts.append(f"City: {salon['address_city']}")
    if salon.get("rating_google"):
        parts.append(f"Rating: {float(salon['rating_google']):.1f}/5 ({salon.get('rating_count', 0)} reviews)")
    if services:
        parts.append(f"Services: {', '.join(services[:8])}")
    if salon.get("price_level"):
        levels = {1: "budget", 2: "mid-range", 3: "upscale", 4: "luxury"}
        parts.append(f"Price level: {levels.get(salon['price_level'], '')}")
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Max salons to process (0 = all)")
    parser.add_argument("--dry-run", action="store_true", help="Show prompts without calling API")
    parser.add_argument("--batch-size", type=int, default=5, help="Commit every N salons")
    args = parser.parse_args()

    client = get_anthropic_client() if not args.dry_run else None
    if not client and not args.dry_run:
        print("ERROR: No Anthropic auth found. Set ANTHROPIC_API_KEY or log in with Claude Code.")
        sys.exit(1)

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Load salons without descriptions
    query = """
        SELECT s.id, s.name, s.address_city, s.rating_google, s.rating_count, s.price_level,
               array_agg(sv.name ORDER BY sv.price_from) FILTER (WHERE sv.name IS NOT NULL) as service_names
        FROM salons s
        LEFT JOIN services sv ON sv.salon_id = s.id AND sv.is_active = true
        WHERE s.is_active = true
          AND (s.description IS NULL OR s.description = '')
          AND (s.description_el IS NULL OR s.description_el = '')
        GROUP BY s.id, s.name, s.address_city, s.rating_google, s.rating_count, s.price_level
        ORDER BY s.rating_count DESC NULLS LAST
    """
    if args.limit:
        query += f" LIMIT {args.limit}"

    cur.execute(query)
    salons = cur.fetchall()
    logger.info("Salons to process: %d", len(salons))

    if args.dry_run:
        for s in salons[:3]:
            services = s["service_names"] or []
            prompt = build_prompt(s, services)
            print(f"\n=== {s['name']} (id={s['id']}) ===")
            print(prompt)
        print(f"\n[dry-run] Would process {len(salons)} salons")
        # Estimate cost
        avg_input = 250
        avg_output = 300
        total_in = len(salons) * avg_input / 1_000_000
        total_out = len(salons) * avg_output / 1_000_000
        cost = total_in * 0.80 + total_out * 4.00
        print(f"Estimated cost: ${cost:.2f} (Haiku 4.5 pricing)")
        return

    ok = 0
    errors = 0

    for i, salon in enumerate(salons):
        services = salon["service_names"] or []
        user_msg = build_prompt(salon, services)

        try:
            client = get_anthropic_client()
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=400,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            )
            raw = msg.content[0].text.strip()

            # Parse JSON response
            # Strip markdown code blocks if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            result = json.loads(raw)

            desc_el = result.get("el", "").strip()
            desc_en = result.get("en", "").strip()

            if desc_el or desc_en:
                cur.execute(
                    """UPDATE salons
                       SET description_el = COALESCE(NULLIF(%s,''), description_el),
                           description    = COALESCE(NULLIF(%s,''), description)
                       WHERE id = %s""",
                    (desc_el or None, desc_en or None, salon["id"]),
                )
                ok += 1

                if ok % args.batch_size == 0:
                    conn.commit()
                    logger.info("Progress: %d/%d (errors: %d)", ok, len(salons), errors)

        except json.JSONDecodeError as e:
            logger.warning("JSON parse error for salon %d: %s | raw: %s", salon["id"], e, raw[:100])
            errors += 1
        except Exception as e:
            logger.error("Error for salon %d (%s): %s", salon["id"], salon["name"], e)
            errors += 1
            err_str = str(e).lower()
            if "529" in str(e) or "rate_limit" in err_str or "overloaded" in err_str:
                logger.info("Overloaded/rate-limited, waiting 60s...")
                time.sleep(60)
            elif "401" in str(e) or "authentication" in err_str or "invalid" in err_str:
                logger.warning("Auth error — token may have expired. Waiting 30s for refresh...")
                time.sleep(30)
                # Force client re-creation on next request
                global _current_token, _client
                _current_token = None
                _client = None

        # Respect rate limit: 50 req/min = 1.2s between requests
        time.sleep(1.3)

    conn.commit()
    cur.close()
    conn.close()
    logger.info("Done: %d ok, %d errors", ok, errors)


if __name__ == "__main__":
    main()
