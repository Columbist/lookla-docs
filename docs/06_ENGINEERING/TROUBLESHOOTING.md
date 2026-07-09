---
title: Troubleshooting Log
status: Approved
version: 1.0
owner: Engineering
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 06_ENGINEERING/AUDIT.md
implementation_status: N/A — operational reference
---

# Lookla — Troubleshooting Log

> Engineering document. Describes known issues and their resolutions.  
> Add entries at the bottom when a new issue is resolved.

---

## Server

### Disk almost full
**Symptom:** `df -h` shows 83%+ usage
**Cause:** Docker build cache accumulation
**Resolution:**
```bash
docker builder prune -f
docker image prune
```

### OOM crash (2026-06-02)
**Symptom:** Server went down; `beauty_crawler_worker` using 741MB without limit
**Resolution:** Memory limits added to `docker-compose.yml`
```yaml
deploy:
  resources:
    limits:
      memory: 500m  # crawler_worker
```

### PM2 does not start after reboot
**Symptom:** tiktok-bot not started; systemd error
**Cause:** Stale `/root/.pm2/pm2.pid` after OOM crash
**Resolution:** Added to `/etc/systemd/system/pm2-root.service`:
```ini
ExecStartPre=/bin/rm -f /root/.pm2/pm2.pid
```

---

## Docker / PostgreSQL

### beauty_db does not start
```bash
docker compose logs beauty_db
# Common causes:
# - pgdata volume corrupted → restore from backup
# - wrong DB_PASSWORD in .env
```

### Connect to DB from host
```bash
docker exec beauty_db psql -U beauty -d beauty_gr -c "SELECT COUNT(*) FROM salons;"
```

### Schema change (no Alembic yet)
```bash
# Direct SQL — document in DECISION_LOG before running
docker exec beauty_db psql -U beauty -d beauty_gr -c "ALTER TABLE ..."
```

---

## Xray (do not modify — diagnostics only)

### Xray not working
```bash
systemctl status xray
journalctl -u xray -n 50
# Config: /usr/local/etc/xray/config.json
# Ports: 1080 (socks), 4443 (vless), 10085 (dokodemo) — localhost only
```

### Nginx conflict with Xray
Should not occur — Xray listens on 127.0.0.1 only. If conflict:
```bash
nginx -t
cat /etc/nginx/sites-enabled/*
```

---

## Known Architecture Decisions

### PostGIS not installed (postgres:16-alpine)
**Symptom:** `ERROR: type "geography" does not exist`
**Resolution:** Using Haversine formula in pure SQL (±0.5% accuracy to 100km — sufficient for production).
**Date:** 2026-06-17
**Note:** PostGIS can be added later by switching to `postgis/postgis:16-alpine` during a planned migration.

---

## Entry Template

```
### [Issue title]
**Symptom:** [What the user/developer sees]
**Cause:** [Why it happens]
**Resolution:** [Specific commands or changes]
**Date:** YYYY-MM-DD
```

---

*Last updated: 2026-07-09*
