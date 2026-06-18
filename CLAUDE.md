# Lookla — Beauty Marketplace Greece
## Инженерный мануал (живой документ, обновляется при каждом изменении)

---

## Сервер

```
Host:    10.10.0.1 (columbxray)
OS:      Ubuntu 24.04.4 LTS
RAM:     2 GB (1 vCPU)
Disk:    20 GB SSD (~4 GB свободно)
SSH:     root@10.10.0.1
```

### Занятые порты (не трогать)
| Порт | Процесс | Примечание |
|------|---------|-----------|
| 22 | sshd | SSH |
| 80/443 | Nginx | web |
| 1080 | Xray SOCKS | только 127.0.0.1 |
| 4443 | Xray VLESS | только 127.0.0.1 |
| 8888 | Tinyproxy | HTTP proxy |
| 10085 | Xray dokodemo | только 127.0.0.1 |
| 5432 | PostgreSQL (Docker) | beauty_db |
| 6379 | Redis (Docker) | beauty_redis |

### Наши порты (beauty-gr проект)
| Порт | Сервис | Статус |
|------|---------|--------|
| 8001 | FastAPI (beauty_api) | ЗАПЛАНИРОВАН |
| 3000 | Next.js (beauty_web) | ЗАПЛАНИРОВАН |

### Не связанные сервисы на этом сервере
- **tiktok-bot** — PM2, `/opt/tiktok-bot`, постит картинки в Telegram. Не трогать.
- **Xray** — VPN/proxy, `/usr/local/etc/xray/config.json`. Не трогать.
- **Tinyproxy** — HTTP proxy на :8888. Не трогать.

---

## База данных

```
Container: beauty_db (PostgreSQL 16)
DB:        beauty_gr
User:      beauty
Password:  из .env (DB_PASSWORD)
Host:      localhost:5432 (снаружи Docker) / db:5432 (внутри Docker)
```

### Существующие таблицы (созданы crawler-ом)
- `salons` — 1016 записей, 99% с телефоном и координатами
- `photos` — 9023 записей (URL от Google/Treatwell, не локальные файлы)
- `reviews` — агрегированные с внешних источников
- `salon_hours` — часы работы
- `services` — 0 записей (поля есть, данных нет)
- `service_categories` — заполнены (hair, nails, skin, etc.)
- `staff` — профили сотрудников
- `social_links` — ссылки соцсетей
- `salon_tags` / `tags` — теги (parking, wifi, etc.)
- `salon_categories` — связь салон↔категория
- `crawler_sources` — источники краулера
- `users` — placeholder (пустая)
- `salon_owners` — связь user↔salon (пустая)

### Запланированные новые таблицы (Alembic миграции)
- `professionals` — мастера с выездом/домашняя студия
- `professional_portfolio` — портфолио фото до/после
- `professional_availability` — расписание мастеров
- `appointments` — записи (booking)
- `staff_schedules` — расписание сотрудников салона
- `conversations` — треды переписки клиент↔салон/мастер
- `messages` — сообщения в переде
- `availability_requests` — мягкий запрос «хочу записаться»
- `translation_cache` — кешированные переводы (DeepL)
- `subscription_plans` — тарифы
- `salon_subscriptions` — подписки салонов
- `moderation_queue` — очередь модерации контента
- `reports` — жалобы пользователей на салоны
- `webhooks` — исходящие вебхуки (для интеграций)
- `event_log` — лог всех бизнес-событий

---

## Docker Compose

Файл: `/root/beauty-gr/docker-compose.yml`

### Запущенные контейнеры
| Контейнер | Образ | Память | Статус |
|-----------|-------|--------|--------|
| beauty_db | postgres:16-alpine | лимит 300 MB | healthy |
| beauty_redis | redis:7-alpine | лимит 150 MB | healthy |
| beauty_crawler | ./crawler | лимит 200 MB | running |
| beauty_crawler_worker | ./crawler | лимит 500 MB | running |

### Запланированные контейнеры
| Контейнер | Образ | Память | Порт |
|-----------|-------|--------|------|
| beauty_api | ./backend | лимит 200 MB | 8001 |
| beauty_web | ./frontend | лимит 300 MB | 3000 |

### Полезные команды
```bash
cd /root/beauty-gr
docker compose ps
docker compose logs -f beauty_api
docker compose restart beauty_api
docker compose exec beauty_db psql -U beauty -d beauty_gr
```

---

## Структура проекта

```
/root/beauty-gr/
├── CLAUDE.md              ← этот файл (мой мануал)
├── DOCS/
│   ├── API.md             ← все endpoints
│   ├── DATABASE.md        ← схема БД детально
│   ├── FEATURES.md        ← что реализовано
│   ├── TROUBLESHOOTING.md ← решённые проблемы
│   ├── DEPLOYMENT.md      ← деплой и переменные
│   └── AI_SYSTEM_PROMPT.md← системный промпт бота
├── backend/               ← FastAPI (Python 3.12)
│   ├── app/
│   │   ├── main.py
│   │   ├── models/
│   │   ├── routers/
│   │   ├── services/
│   │   └── core/
│   ├── alembic/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/              ← Next.js 14 (TypeScript)
│   ├── src/
│   │   ├── app/           ← App Router
│   │   ├── components/
│   │   ├── lib/
│   │   └── messages/      ← i18n: el.json, en.json, ru.json, uk.json
│   ├── Dockerfile
│   └── package.json
├── mobile/                ← React Native + Expo (позже)
├── crawler/               ← существующие краулеры (не трогать структуру)
├── db/
│   ├── init.sql           ← начальная схема (уже применена)
│   └── migrations/        ← Alembic миграции (новые изменения)
├── nginx/
│   └── kallos.conf        ← конфиг для нашего сайта
├── scripts/
│   ├── backup.sh          ← ежедневный бэкап БД
│   └── test_restore.sh    ← тест восстановления
└── .env                   ← секреты (не в git)
```

---

## Nginx

Конфиг: `/etc/nginx/sites-enabled/default` (дефолтный, пустой)
Добавить: `/etc/nginx/sites-available/lookla` → symlink в sites-enabled

```nginx
# /etc/nginx/sites-available/lookla
server {
    listen 80;
    server_name lookla.gr www.lookla.gr;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl;
    server_name lookla.gr www.lookla.gr;
    # SSL через Cloudflare Origin Certificate
    location /api/ { proxy_pass http://127.0.0.1:8001; }
    location /     { proxy_pass http://127.0.0.1:3000; }
}
```

---

## Технологический стек

### Backend
- **Python 3.12** + **FastAPI** + **Uvicorn**
- **SQLAlchemy 2.0** (уже используется в crawler)
- **Alembic** — миграции
- **Pydantic v2** — валидация
- **Celery** + **Redis** (уже запущены) — фоновые задачи
- **python-jose** — JWT токены
- **passlib[bcrypt]** — хеширование паролей
- **boto3** — Cloudflare R2 (S3-совместимый)
- **httpx** — HTTP клиент (DeepL API, внешние сервисы)

### Frontend
- **Next.js 14** (App Router) + **TypeScript**
- **Tailwind CSS** + **shadcn/ui**
- **next-intl** — i18n (el/en/ru/uk)
- **react-leaflet** + **OpenStreetMap** — карты (бесплатно)
- **leaflet.markercluster** — кластеризация точек на карте
- **TanStack Query** — data fetching + cache
- **react-hook-form** + **zod** — формы
- **Zustand** — глобальный state

### Mobile (Sprint 10)
- **Expo SDK 51+** + **React Native**
- **Expo Router** — навигация
- **NativeWind** — Tailwind для RN
- **react-native-maps** — карты
- **Expo Push Notifications** — push (бесплатно)
- **expo-secure-store** — хранение токенов

### Внешние сервисы
| Сервис | Для чего | Лимит бесплатного |
|--------|---------|-------------------|
| Cloudflare | DNS/CDN/SSL/Turnstile | Бесплатно полностью |
| Cloudflare R2 | Медиа-файлы | 10 GB / 1M ops day |
| Backblaze B2 | Бэкапы БД | 10 GB |
| Brevo | Email (транзакционный) | 300 email/день |
| DeepL API | Переводы контента | 500k chars/мес |
| OpenAI Moderation | Модерация текста | Бесплатно |
| Google Vision | Модерация изображений | 1000 req/мес |
| Stripe | Платежи | 0€ фикс + 1.5%+€0.25 |
| Meta WhatsApp API | OTP + уведомления | 1000 conv/мес |
| Oracle Cloud | Резервный сервер | Всегда бесплатно |

---

## Переводы (Translation Engine)

### Стратегия
- **UI strings** → статические JSON файлы (`messages/el.json` etc.), не требуют API
- **Контент салонов** (описания, услуги) → DeepL API, кешируется в `translation_cache`
- **Отзывы** → DeepL, переводятся лениво (при первом просмотре другим языком)
- **Сообщения в чате** → по кнопке «Перевести» (не авто), DeepL
- **Данные краулера** → Greek оригинал, переводы генерируются фоново (Celery task)

### Маркировка переведённого контента
```
[🌐 Переведено с греческого]   ← маленький badge под текстом
[Показать оригинал]            ← ссылка рядом
```
Пользователь видит: если контент на его языке — без пометки. Если переведён — badge + возможность увидеть оригинал.

### DeepL Free (500k символов/мес)
Подсчёт: описание салона ~500 символов × 1016 салонов × 3 языка = ~1.5M chars.
Решение: переводим постепенно по Celery queue, приоритет — salons с фото и рейтингом.
При исчерпании лимита — fallback на LibreTranslate (self-hosted, бесплатно, качество ниже).

### Кеш переводов
```sql
translation_cache (source_hash, source_lang, target_lang, translated_text, provider)
-- SHA256(source_text + target_lang) как уникальный ключ
-- Переводим один раз, храним навсегда (или до изменения оригинала)
```

---

## Платёжная система (архитектура)

Абстрактный интерфейс `PaymentProvider` — первая реализация Stripe, крипта позже.

```python
# app/services/payments/base.py
class PaymentProvider(ABC):
    async def create_subscription(self, user_id, plan_id) -> PaymentSession: ...
    async def cancel_subscription(self, sub_id) -> bool: ...
    async def handle_webhook(self, payload, sig) -> PaymentEvent: ...
    async def create_one_time(self, amount_eur, description) -> PaymentSession: ...

# Активный провайдер выбирается через PAYMENT_PROVIDER env var
# 'stripe' | 'nowpayments' | 'btcpay' | 'coinbase'
```

**Тарифы:**
| Plan | Цена | Онлайн-запись | Мультимастер | Featured |
|------|------|:---:|:---:|:---:|
| Free | 0€ | — | — | — |
| Pro (салон) | 29€/мес | ✓ | — | — |
| Business (салон) | 59€/мес | ✓ | ✓ | ✓ |
| Pro (мастер) | 14€/мес | ✓ | n/a | — |

---

## Языки

| Код | Язык | Приоритет | Где нужен |
|-----|------|-----------|-----------|
| el | Греческий | 1 | UI, SEO, email, данные |
| en | Английский | 2 | UI, App Store, туристы |
| ru | Русский | 3 | UI, email (диаспора ~200k) |
| uk | Украинский | 4 | UI, email (диаспора ~40k) |

URL структура: `/el/`, `/en/`, `/ru/`, `/uk/` + `hreflang` теги.
Определение языка: `Accept-Language` header → cookie → default `el`.
Выбор при первом запуске (web: плашка, app: onboarding экран).

---

## Безопасность

### Защита форм
- **Cloudflare Turnstile** на всех публичных формах (регистрация, запись, отзыв)
- **Honeypot** поля во всех формах (скрытые, боты заполняют)
- **Rate limiting** через Redis (SlowAPI middleware):
  - 5 регистраций / IP / час
  - 10 API запросов / IP / сек
  - 3 неудачных логина → пауза 15 мин

### Модерация
- **Текст:** OpenAI Moderation API (бесплатно) → auto-flag при score > 0.8
- **Изображения:** Google Vision Safe Search (1000/мес) → LIKELY/VERY_LIKELY → queue
- **Очередь:** `moderation_queue` → admin проверяет → approve/reject

### Бан-листы
- IP rate bans: Redis TTL (авто-истекают)
- Permanent bans: таблица в PostgreSQL, admin управляет
- Одноразовые email: disposable-email-domains список (~3000 доменов)

---

## Бэкапы

```bash
# Cron: 0 3 * * * /opt/backup/beauty_backup.sh
# PostgreSQL dump → gzip → Backblaze B2
# Политика: 7 daily + 4 weekly + 12 monthly
# Тест восстановления: 1-е число каждого месяца
# Медиа (R2): версионирование объектов включено в настройках
```

---

## Резервный сервер

**Oracle Cloud Always Free** — зарегистрировать при первой возможности:
- 4 vCPU ARM + 24 GB RAM (Ampere A1)
- 200 GB block storage
- 10 TB/мес egress
- Использование: медиа-сервер и/или migration target

**Миграция основного сервера:**
1. Всё в Docker Compose → portable
2. `pg_dump | psql` на новый хост
3. Медиа в R2 — URL не меняются
4. DNS через Cloudflare TTL=60 → мгновенное переключение

---

## Интеграции (будущие, заложены в архитектуру)

- **EventBus:** все booking события → `event_log` → исходящие webhooks
- **Таблица `webhooks`** создана с первого дня, просто пустая
- При появлении запроса от салона (Fresha, Treatwell, кастомная CRM) — добавляем webhook subscriber без изменения ядра
- **Крипто-платежи:** NOWPayments / BTCPay / Coinbase Commerce — реализуют `PaymentProvider` интерфейс

---

## Известные проблемы и решения

| Проблема | Решение | Дата |
|---------|---------|------|
| *заполняется по мере разработки* | | |

---

## Changelog

| Версия | Дата | Что сделано |
|--------|------|------------|
| 0.4 | 2026-06-18 | Sprint 4-5: Owner claiming, master registration, booking system |
| 0.3 | 2026-06-18 | Sprint 3: Auth (JWT, register, login, OAuth, rate limiting) |
| 0.2 | 2026-06-18 | Sprint 1-2: FastAPI + Next.js (home, search, salon detail, map, 4 langs) |
| 0.1 | 2026-06-17 | Инициализация проекта, создан CLAUDE.md |
