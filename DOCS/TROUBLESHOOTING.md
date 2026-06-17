# Lookla — Troubleshooting Log
## Известные проблемы и решения

---

## Сервер

### Disk почти полный (83% при старте проекта)
**Симптом:** `df -h` показывает 83% / ~3.4 GB свободно
**Причина:** Docker build cache накопил 4+ GB
**Решение:**
```bash
docker builder prune -f        # ~800 MB кеша
docker image prune             # dangling images
# Должно стать > 4.5 GB свободно
```

### OOM crash (был 2026-06-02)
**Симптом:** сервер упал, beauty_crawler_worker использовал 741 MB без лимита
**Решение:** добавлены memory limits в docker-compose.yml
```yaml
deploy:
  resources:
    limits:
      memory: 500m  # worker
      # crawler: 200m, db: 300m, redis: 150m
```

### PM2 не стартует после перезагрузки
**Симптом:** tiktok-bot не запустился, systemd показывал ошибку
**Причина:** stale `/root/.pm2/pm2.pid` файл после OOM crash
**Решение:** в `/etc/systemd/system/pm2-root.service`:
```ini
ExecStartPre=/bin/rm -f /root/.pm2/pm2.pid
```

---

## Docker / PostgreSQL

### beauty_db не запускается
```bash
docker compose logs beauty_db
# Частые причины:
# - pgdata volume corrupted → restore from backup
# - неверный DB_PASSWORD в .env
```

### Подключение к БД из хоста
```bash
# НЕ через docker exec psql напрямую — используй:
docker exec beauty_db psql -U beauty -d beauty_gr -c "SELECT COUNT(*) FROM salons;"
```

### Миграция Alembic упала
```bash
cd /root/beauty-gr/backend
# Посмотреть текущую версию
alembic current
# Откатить последнюю
alembic downgrade -1
# История миграций
alembic history
```

---

## Xray (не трогать, только диагностика)

### Xray не работает
```bash
systemctl status xray
journalctl -u xray -n 50
# Конфиг: /usr/local/etc/xray/config.json
# Порты: 1080 (socks), 4443 (vless), 10085 (dokodemo) — все только localhost
```

### Nginx конфликтует с Xray
**Не должно происходить** — Xray слушает только 127.0.0.1, nginx роутит по server_name.
Если всё же конфликт — проверить nginx конфиг:
```bash
nginx -t
cat /etc/nginx/sites-enabled/*
```

---

## Добавлять сюда при каждой новой решённой проблеме
Формат:
```
### Название проблемы
**Симптом:** что видит пользователь/разработчик
**Причина:** почему происходит
**Решение:** конкретные команды/изменения
**Дата:** YYYY-MM-DD
```
