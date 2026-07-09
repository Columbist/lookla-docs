"""
Celery Beat scheduler entrypoint.
Runs in the `crawler` container alongside the Celery worker.
"""
import logging
import os
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

if __name__ == "__main__":
    # Start Celery Beat
    cmd = [
        sys.executable, "-m", "celery",
        "-A", "beauty_crawler.celery_app",
        "beat", "--loglevel=info",
    ]
    logging.info("Starting Celery Beat: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)
