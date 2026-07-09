#!/usr/bin/env python3
"""Generate static sitemap.xml from DB slugs. Run after frontend build."""
import psycopg2
import os
import sys

BASE_URL = "https://lookla.gr"
LOCALES = ["el", "en", "ru", "uk"]
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

def locale_path(locale, path):
    return f"{BASE_URL}{path}" if locale == "el" else f"{BASE_URL}/{locale}{path}"

entries = []

static_pages = ["", "/search", "/masters", "/login", "/register"]
for locale in LOCALES:
    for page in static_pages:
        entries.append({
            "url": locale_path(locale, page or "/"),
            "changefreq": "daily" if page == "" else "weekly",
            "priority": "1.0" if page == "" else "0.7",
        })

try:
    conn = psycopg2.connect(
        host="127.0.0.1", port=5432, dbname="beauty_gr",
        user="beauty", password="changeme_strong_password"
    )
    cur = conn.cursor()
    cur.execute("SELECT slug, updated_at FROM salons WHERE slug IS NOT NULL AND slug != '' ORDER BY id")
    salons = cur.fetchall()
    conn.close()
    for slug, updated_at in salons:
        for locale in LOCALES:
            entry = {
                "url": locale_path(locale, f"/salons/{slug}"),
                "changefreq": "monthly",
                "priority": "0.8",
            }
            if updated_at:
                entry["lastmod"] = updated_at.strftime("%Y-%m-%d")
            entries.append(entry)
    print(f"  {len(salons)} salons added to sitemap")
except Exception as e:
    print(f"  DB unavailable, using static pages only: {e}", file=sys.stderr)

lines = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for e in entries:
    lines.append("  <url>")
    lines.append(f"    <loc>{e['url']}</loc>")
    if "lastmod" in e:
        lines.append(f"    <lastmod>{e['lastmod']}</lastmod>")
    lines.append(f"    <changefreq>{e['changefreq']}</changefreq>")
    lines.append(f"    <priority>{e['priority']}</priority>")
    lines.append("  </url>")
lines.append("</urlset>")
xml = "\n".join(lines)

public_dir = os.path.join(FRONTEND_DIR, "public")
os.makedirs(public_dir, exist_ok=True)

out_path = os.path.join(public_dir, "sitemap.xml")
with open(out_path, "w") as f:
    f.write(xml)
print(f"  Written {len(entries)} entries → {out_path}")
