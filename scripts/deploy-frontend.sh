#!/bin/bash
set -e
cd /root/beauty-gr/frontend

echo "Building..."
NODE_OPTIONS="--max-old-space-size=512" npm run build

echo "Generating sitemap..."
python3 /root/beauty-gr/scripts/generate-sitemap.py

echo "Copying static assets..."
cp -r .next/static .next/standalone/.next/static
[ -d public ] && cp -r public .next/standalone/public || true

echo "Restarting PM2..."
pm2 restart lookla-web

echo "Done. Testing..."
sleep 4
curl -sI http://127.0.0.1:3000/ | grep "HTTP/"
