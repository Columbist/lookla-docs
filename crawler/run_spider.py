#!/usr/bin/env python3
"""
Manual CLI to run individual spiders without Celery.

Usage:
  python run_spider.py google           # Google Places
  python run_spider.py vrisko           # vrisko.gr
  python run_spider.py treatwell        # Treatwell.gr
  python run_spider.py all              # all sources sequentially
"""
import logging
import sys
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

SPIDERS = {
    "google":         "beauty_crawler.spiders.google_places",
    "foursquare":     "beauty_crawler.spiders.foursquare",
    "vrisko":         "beauty_crawler.spiders.vrisko",
    "xo":             "beauty_crawler.spiders.xo",
    "beautyproject":  "beauty_crawler.spiders.beauty_project",
    "treatwell":      "beauty_crawler.spiders.treatwell",
    "facebook":       "beauty_crawler.spiders.facebook",
}

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    targets = list(SPIDERS.keys()) if target == "all" else [target]

    for name in targets:
        if name not in SPIDERS:
            print(f"Unknown spider '{name}'. Options: {list(SPIDERS.keys())} or 'all'")
            sys.exit(1)
        print(f"\n{'='*50}")
        print(f"Running spider: {name}")
        print(f"{'='*50}")
        mod = __import__(SPIDERS[name], fromlist=["run"])
        mod.run()

if __name__ == "__main__":
    main()
