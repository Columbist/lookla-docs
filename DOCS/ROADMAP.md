# Lookla — Roadmap & Task Breakdown
## Lead Engineer: Claude | Product Owner: columb@europe.com
## Последнее обновление: 2026-06-17

---

## Статусы
- `[ ]` — не начато
- `[→]` — в работе
- `[x]` — готово
- `[~]` — отложено / deprioritized

---

# SPRINT 0 — Фундамент (3 дня)
**Цель:** чистый сервер, структура проекта, CI/CD скелет.

## INF-01: Очистка сервера
- [ ] `docker builder prune -f` → освободить ~800 MB кеша
- [ ] `docker image prune` — удалить dangling images
- [ ] Настроить logrotate для `/root/beauty-gr/crawler/logs/`
- [ ] Проверить disk после: должно быть > 5 GB свободно

## INF-02: Git репозиторий
- [ ] Создать private GitHub repo `lookla-platform`
- [ ] Инициализировать git в `/root/beauty-gr/`
- [ ] Добавить `.gitignore` (исключить `.env`, `__pycache__`, `node_modules`, `dist/`, `*.pyc`)
- [ ] Добавить `.env.example` с описанием всех переменных
- [ ] Первый коммит: текущая структура + CLAUDE.md + DOCS/

## INF-03: GitHub Actions CI
- [ ] `.github/workflows/ci.yml`
  - Backend: `ruff` lint + `pytest` (пустой test suite для старта)
  - Frontend: `tsc --noEmit` + `eslint`
- [ ] `.github/workflows/deploy.yml`
  - Триггер: push to `main`
  - Action: SSH на сервер → `git pull` → `docker compose up -d --build`

## INF-04: Nginx конфиг
- [ ] Создать `/etc/nginx/sites-available/lookla`
  - Роутинг: `/api/` → `:8001`, `/` → `:3000`
  - Заглушка 502 пока сервисы не запущены
- [ ] Symlink → `sites-enabled/kallos`
- [ ] Cloudflare: добавить домен, настроить DNS A-запись
- [ ] SSL: Cloudflare Origin Certificate → Nginx

## INF-05: Переменные окружения
- [ ] Дополнить `/root/beauty-gr/.env`:
  ```
  # Existing
  DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
  REDIS_URL

  # New — Backend
  SECRET_KEY=          # JWT secret (openssl rand -hex 32)
  ALLOWED_ORIGINS=     # https://lookla.gr,https://www.lookla.gr

  # Auth
  GOOGLE_CLIENT_ID=
  GOOGLE_CLIENT_SECRET=
  APPLE_CLIENT_ID=
  APPLE_TEAM_ID=
  APPLE_KEY_ID=
  APPLE_PRIVATE_KEY=

  # Media
  R2_ACCOUNT_ID=
  R2_ACCESS_KEY=
  R2_SECRET_KEY=
  R2_BUCKET=lookla-media
  R2_PUBLIC_URL=https://media.lookla.gr

  # Email
  BREVO_API_KEY=
  BREVO_SENDER_EMAIL=noreply@lookla.gr

  # Translations
  DEEPL_API_KEY=

  # Moderation
  OPENAI_API_KEY=
  GOOGLE_VISION_API_KEY=

  # Payments
  STRIPE_SECRET_KEY=
  STRIPE_WEBHOOK_SECRET=
  PAYMENT_PROVIDER=stripe

  # WhatsApp OTP
  META_WHATSAPP_TOKEN=
  META_PHONE_NUMBER_ID=

  # Cloudflare Turnstile
  TURNSTILE_SECRET_KEY=

  # Sentry
  SENTRY_DSN=
  ```

---

# SPRINT 1 — База данных + FastAPI скелет (2 недели)
**Цель:** API работает, возвращает данные из БД. Swagger доступен.

## DB-01: Alembic инициализация
- [ ] `alembic init alembic` в `/root/beauty-gr/backend/`
- [ ] `env.py` настроить на SQLAlchemy models
- [ ] Baseline миграция существующей схемы (без изменений)
- [ ] Проверить: `alembic upgrade head` проходит без ошибок

## DB-02: Новые таблицы (миграция)
- [ ] `professionals` + `professional_portfolio` + `professional_availability`
- [ ] `appointments` + `staff_schedules`
- [ ] `conversations` + `messages`
- [ ] `availability_requests`
- [ ] `translation_cache`
- [ ] `subscription_plans` + `salon_subscriptions`
- [ ] `moderation_queue` + `reports`
- [ ] `webhooks` + `event_log`
- [ ] Добавить в `salons`: `description_ru`, `description_uk`, `needs_review` bool
- [ ] Добавить в `social_links`: расширить допустимые платформы (messenger, viber, whatsapp, tiktok)
- [ ] Добавить в `users`: `preferred_language`, `viber_phone`, `whatsapp_phone`, `avatar_url`

## BE-01: FastAPI проект
- [ ] Создать `/root/beauty-gr/backend/app/main.py`
  - Sentry SDK init
  - CORS middleware
  - `/api/health` endpoint
- [ ] `Dockerfile` для backend
- [ ] Добавить `beauty_api` в `docker-compose.yml` (порт 8001, memory_limit 200m)
- [ ] Проверить: `curl localhost:8001/api/health` → `{"status":"ok"}`

## BE-02: Публичные read-only endpoints
- [ ] `GET /api/salons` — список (пагинация: page, limit; фильтр: city, category_slug, min_rating, max_price_level)
- [ ] `GET /api/salons/{id_or_slug}` — детали + hours + photos + services + social_links + reviews count
- [ ] `GET /api/salons/{id}/photos`
- [ ] `GET /api/salons/{id}/reviews`
- [ ] `GET /api/search` — полнотекстовый (PostgreSQL FTS unaccent)
  - params: `q`, `city`, `category`, `lat`, `lng`, `radius_km`, `lang`
  - returns: salons + professionals в одном ответе с `type` полем
- [ ] `GET /api/professionals` — список (пагинация + фильтры)
- [ ] `GET /api/professionals/{id_or_slug}` — детали + portfolio + availability
- [ ] `GET /api/cities` — список городов с количеством (salons + professionals)
- [ ] `GET /api/categories` — дерево категорий на нужном языке
- [ ] `GET /api/sitemap-data` — данные для sitemap (slug + updated_at)

## BE-03: Geo-поиск
- [ ] Endpoint `GET /api/search?lat=&lng=&radius_km=` — PostGIS ST_DWithin
- [ ] Для professionals: учитывать `service_radius_km` (мастер с радиусом 15км виден в зоне)
- [ ] Сортировка по расстоянию (ST_Distance)

## BE-04: Документация API
- [ ] Swagger автоматический (`/api/docs`)
- [ ] Заполнить `DOCS/API.md` всеми endpoints (curl примеры)

---

# SPRINT 2 — Публичный каталог (2 недели)
**Цель:** сайт с поиском, картой и карточками. Открыть для индексации Google.

## FE-01: Next.js проект
- [ ] Создать `/root/beauty-gr/frontend/`
  - `npx create-next-app@latest --typescript --tailwind --app`
  - установить: shadcn/ui, next-intl, react-leaflet, TanStack Query, zustand, react-hook-form, zod
- [ ] `Dockerfile` для frontend
- [ ] Добавить `beauty_web` в `docker-compose.yml` (порт 3000, memory_limit 300m)
- [ ] `next-intl` настройка: routing по `/[locale]/`, сообщения в `messages/`
- [ ] 4 файла переводов: `el.json`, `en.json`, `ru.json`, `uk.json` (UI строки)
- [ ] Language switcher компонент в header

## FE-02: Страницы каталога
- [ ] `/[locale]` — главная: поиск-строка + популярные города + категории + CTA
- [ ] `/[locale]/search` — результаты: список + карта (переключение), фильтры сайдбар
- [ ] `/[locale]/salons/[slug]` — профиль салона:
  - Фото галерея (lightbox)
  - Описание (с badge «Переведено с греческого» если переведено)
  - Услуги с ценами
  - Часы работы
  - Карта (Leaflet, маркер)
  - Кнопки: Позвонить / Viber / WhatsApp / Messenger / Сайт
  - Соцсети (иконки-ссылки)
  - Отзывы (агрегат)
  - Кнопка «Сообщить о проблеме»
  - Кнопка «Написать» (внутренний чат, требует логина)
- [ ] `/[locale]/masters/[slug]` — профиль мастера:
  - Аватар + имя + специализация
  - Портфолио (masonry grid, before/after lightbox)
  - Зона покрытия на Leaflet карте (круг радиуса)
  - Услуги + цены
  - Расписание доступности
  - Соцсети (Instagram с oEmbed preview)
  - Кнопки контакта (как у салона)
- [ ] `/[locale]/[city]/[category]` — SEO-страницы (SSG, generateStaticParams)

## FE-03: Карта
- [ ] Leaflet + OpenStreetMap (бесплатно)
- [ ] Кластеризация маркеров (leaflet.markercluster)
- [ ] Клик на маркер → bottom sheet / sidebar с карточкой
  - Фото + имя + рейтинг + телефон
  - Кнопка «Открыть профиль» → `/salons/[slug]`
- [ ] Для мастеров: круговая зона (L.circle радиус = service_radius_km)
- [ ] Геолокация: кнопка «Рядом со мной»
- [ ] Переключение «Список / Карта» (mobile-friendly)

## FE-04: SEO
- [ ] `generateMetadata()` на каждой странице (title, description, OG)
- [ ] Schema.org `LocalBusiness` JSON-LD на `/salons/[slug]`
- [ ] Schema.org `Person` JSON-LD на `/masters/[slug]`
- [ ] `sitemap.xml` — Next.js App Router sitemap generator (динамический, из API)
- [ ] `robots.txt`
- [ ] `hreflang` теги для всех 4 языков
- [ ] Google Search Console: добавить сайт, сабмитнуть sitemap

## FE-05: Перевод контента
- [ ] Badge компонент `<TranslatedBadge fromLang="el" />` — 🌐 Переведено с греческого
- [ ] Кнопка «Показать оригинал» — toggle между переведённым и оригиналом
- [ ] API: `GET /api/translate?text=&from=el&to=ru` — через DeepL, кеш в translation_cache
- [ ] Celery task: `translate_salon_descriptions` — фоновый перевод всех 1016 салонов

---

# SPRINT 3 — Auth (10 дней)
**Цель:** регистрация, вход всеми методами, JWT, профиль пользователя.

## BE-05: Auth система
- [ ] JWT токены (access 15min, refresh 30 days) в httpOnly cookie
- [ ] `POST /api/auth/register` — email + password + preferred_language
  - Проверка disposable email (список из npm `disposable-email-domains`)
  - Cloudflare Turnstile token валидация
  - Отправка verify email (Brevo template)
- [ ] `POST /api/auth/verify-email` — подтверждение токена
- [ ] `POST /api/auth/login` — email + password
  - Rate limit: 3 неудачи → Redis 15min lock
- [ ] `POST /api/auth/logout` — revoke refresh token
- [ ] `POST /api/auth/refresh` — обновить access token
- [ ] `GET /api/auth/me` — текущий пользователь

## BE-06: OAuth
- [ ] `GET /api/auth/google` → redirect → `GET /api/auth/google/callback`
  - Если email уже есть — логин; если нет — регистрация
- [ ] `POST /api/auth/apple` — получить identity token, верифицировать
  - Apple требует верификацию через Apple's public keys (JWKS)

## BE-07: Сброс пароля
- [ ] `POST /api/auth/forgot-password` — принимает email или phone
  - Email → ссылка со токеном (Brevo)
  - Phone → OTP 6 цифр → WhatsApp (Meta API) или SMS (Brevo)
- [ ] `POST /api/auth/verify-otp` — проверить OTP
- [ ] `POST /api/auth/reset-password` — установить новый пароль по токену
- [ ] `POST /api/auth/generate-password` — вернуть сгенерированный читаемый пароль (не сохраняет)

## BE-08: Защита форм
- [ ] SlowAPI middleware (rate limiting через Redis)
- [ ] Cloudflare Turnstile server-side validation endpoint
- [ ] Honeypot middleware (проверяет наличие скрытого поля в POST)
- [ ] Disposable email check service

## FE-06: Auth UI
- [ ] Модальное окно: Войти / Зарегистрироваться (tabbed)
- [ ] Форма регистрации: email, password, язык; кнопка «Предложить пароль»
- [ ] Форма логина: email + password
- [ ] Google OAuth кнопка
- [ ] Apple Sign In кнопка (только на iOS/Safari)
- [ ] Форма «Забыл пароль»: email или телефон; выбор канала (Email / WhatsApp / Viber)
- [ ] Страница `/[locale]/verify-email` — подтверждение email
- [ ] Личный кабинет клиента `/[locale]/account`:
  - Мои записи (история + повторная запись)
  - Избранные салоны
  - Настройки (язык, уведомления, контакты)

---

# SPRINT 4 — Бизнес-аккаунты (2 недели)
**Цель:** владельцы салонов и мастера могут управлять своими профилями.

## BE-09: Claiming для салонов
- [ ] `POST /api/salons/{id}/claim` — создать claim request
  - Генерация verification токена
  - Отправить SMS/WhatsApp на phone_primary
  - Или email (если совпадает домен сайта)
- [ ] `POST /api/salons/{id}/claim/verify` — проверить токен
  - Привязать `user_id` → `salon_owners`
  - `is_verified = true`
- [ ] Admin: список pending claims + approve/reject

## BE-10: Owner dashboard API
- [ ] `PUT /api/owner/salon/{id}` — редактировать (auth: salon_owner)
  - name, description_el/en/ru/uk, hours, contact info
  - При изменении description — запустить Celery перевод если нет ru/uk
- [ ] `POST /api/owner/salon/{id}/photos` — загрузить фото
  - Presigned URL → R2 upload
  - После upload: Google Vision moderation проверка
- [ ] `DELETE /api/owner/salon/{id}/photos/{photo_id}`
- [ ] `POST /api/owner/salon/{id}/services` — добавить услугу
- [ ] `PUT /api/owner/salon/{id}/services/{service_id}`
- [ ] `DELETE /api/owner/salon/{id}/services/{service_id}`
- [ ] `PUT /api/owner/salon/{id}/social-links` — обновить соцсети
- [ ] `GET/PUT /api/owner/salon/{id}/staff` — сотрудники

## BE-11: Регистрация мастеров
- [ ] `POST /api/professionals` — создать профиль (auth required)
  - Статус: `pending` → admin review → `active`
- [ ] `PUT /api/professionals/{id}` — редактировать (auth: owner)
- [ ] `POST /api/professionals/{id}/portfolio` — загрузить фото
  - До 20 фото; presigned URL → R2; Vision moderation
- [ ] `DELETE /api/professionals/{id}/portfolio/{photo_id}`
- [ ] `PUT /api/professionals/{id}/availability` — расписание
- [ ] `PUT /api/professionals/{id}/social-links`

## FE-07: Owner dashboard UI
- [ ] `/[locale]/dashboard` — общий дашборд (перенаправляет по роли)
- [ ] `/[locale]/dashboard/salon` — дашборд владельца салона
  - Редактор профиля (tabbed: основное / фото / услуги / сотрудники / соцсети)
  - Загрузчик фото (drag & drop + preview)
  - Редактор услуг (таблица с inline edit)
  - Редактор соцсетей (поля для всех платформ + иконки-превью)
  - Карточка подписки + кнопка апгрейда
- [ ] `/[locale]/dashboard/master` — дашборд мастера
  - Редактор профиля
  - Портфолио (masonry grid с drag-to-reorder, before/after upload)
  - Редактор расписания (7 дней × слоты)
  - Зона покрытия (Leaflet карта + ползунок радиуса)

## FE-08: Claiming UI
- [ ] Кнопка «Это ваш бизнес? Заявить права» на странице салона
- [ ] Мастер регистрации: форма создания профиля мастера
- [ ] Flow верификации: ввод кода

---

# SPRINT 5 — Онлайн-запись (2.5 недели)
**Цель:** клиенты могут записаться онлайн, владельцы управляют расписанием.

## DB-03: Booking таблицы
- [ ] `appointments` — id, salon_id, professional_id, client_user_id, client_name, client_phone, service_id, staff_id, starts_at, ends_at, status (pending/confirmed/cancelled/no_show), notes, source (web/app/manual), created_at
- [ ] `staff_schedules` — staff_id, day_of_week, start_time, end_time, is_available, valid_from, valid_to

## BE-12: Availability API
- [ ] `GET /api/salons/{id}/availability?date=&service_id=&staff_id=`
  - Учитывает: salon_hours + staff_schedules + существующие appointments + duration
  - Возвращает: массив доступных слотов
- [ ] `GET /api/professionals/{id}/availability?date=&service_id=`

## BE-13: Booking API
- [ ] `POST /api/bookings` — создать запись (guest или auth)
  - Валидация слота (race condition защита через DB transaction + SELECT FOR UPDATE)
  - Celery: отправить confirmation email (Brevo template)
  - Celery: уведомить владельца (email + push placeholder)
  - EventBus: emit `booking.created`
- [ ] `GET /api/bookings/{id}` — детали (auth: участник)
- [ ] `DELETE /api/bookings/{id}` — отмена (auth: участник, за N часов до)
- [ ] `GET /api/account/bookings` — история клиента (auth)
- [ ] `GET /api/owner/bookings` — входящие (auth: owner)
  - Фильтры: date, status, staff_id
- [ ] `PATCH /api/owner/bookings/{id}` — confirm/cancel (auth: owner)

## BE-14: Напоминания
- [ ] Celery beat task: каждый час проверяет appointments на завтра
  - Отправить email клиенту «Напоминание: запись завтра в HH:MM»
  - Ссылка «Отменить» + «Добавить в Google Calendar» (iCal link)

## FE-09: Booking виджет
- [ ] Компонент `<BookingWidget salonId={} />` — встроен на страницу салона/мастера
- [ ] Шаги:
  1. Выбор услуги (список с ценой и длительностью)
  2. Выбор мастера (если несколько; «Любой доступный»)
  3. Выбор даты (calendar picker) → загрузка слотов
  4. Выбор времени (grid кнопок)
  5. Контактные данные (имя, телефон, email/whatsapp, комментарий)
  6. Подтверждение + кнопка «Записаться»
- [ ] Ссылка «Добавить в Google/Apple Calendar» в confirmation
- [ ] Страница `/[locale]/booking/[id]` — детали записи

## FE-10: Owner calendar
- [ ] `/[locale]/dashboard/bookings` — список входящих + calendar view
  - Фильтр по мастеру, статусу, дате
  - Кнопки: Подтвердить / Отменить
  - Детали записи в модалке

---

# SPRINT 6 — Чат + Запросы доступности (1.5 недели)
**Цель:** клиент может написать салону/мастеру и запросить время.

## BE-15: Messaging API
- [ ] `POST /api/conversations` — начать переписку (auth, client → salon/professional)
- [ ] `GET /api/conversations` — список тредов (auth)
- [ ] `GET /api/conversations/{id}/messages` — сообщения с пагинацией
- [ ] `POST /api/conversations/{id}/messages` — отправить (text + optional photo)
  - Фото: presigned upload → R2 → Vision moderation
  - Redis INCR `unread:{user_id}` counter
- [ ] `POST /api/conversations/{id}/read` — отметить прочитанным (сбросить counter)
- [ ] `GET /api/account/unread-count` — количество непрочитанных

## BE-16: Availability requests
- [ ] `POST /api/salons/{id}/availability-request`
  - service_notes, preferred_dates (text), client contact
- [ ] `GET /api/owner/availability-requests` — входящие (auth: owner)
- [ ] `POST /api/owner/availability-requests/{id}/propose`
  - proposed_slot: datetime
  - Celery: email + push клиенту «Вам предложили время»
- [ ] `POST /api/availability-requests/{id}/confirm` — клиент подтверждает
  - Создаёт `appointment` автоматически
  - EventBus: emit `booking.created`

## FE-11: Chat UI
- [ ] Кнопка «Написать» на профилях (только auth; если нет — предложить войти)
- [ ] `/[locale]/account/messages` — список переписок
- [ ] `/[locale]/account/messages/[id]` — тред
  - Сообщения timeline
  - Поле ввода + кнопка отправки фото
  - Badge непрочитанных в хедере
  - Polling каждые 10 сек (WebSocket позже)

## FE-12: Availability request UI
- [ ] Кнопка «Хочу записаться» рядом с «Написать»
- [ ] Модалка: 3 поля (услуга / удобное время free-text / комментарий)
- [ ] В Owner dashboard: входящие запросы + кнопка «Предложить слот» (date-time picker)
- [ ] Уведомление клиенту в чате + email: «Ваш запрос обработан, предложено время»
- [ ] Экран финализации записи (предзаполненный booking widget)

---

# SPRINT 7 — Модерация + Репорты (1 неделя)
**Цель:** защита от спама и мусорного контента.

## BE-17: Модерация
- [ ] Service `ModerationService`:
  - `check_text(text)` → OpenAI Moderation API → возвращает is_safe, scores
  - `check_image(url)` → Google Vision Safe Search → is_safe, flags
- [ ] Middleware: при POST любого пользовательского контента → check → если флаг → в очередь
- [ ] Celery task: `process_moderation_queue` — батчевая обработка
- [ ] Email admin при флаге (Brevo)

## BE-18: Reports
- [ ] `POST /api/salons/{id}/report` — жалоба на салон
  - reason enum + description
  - 3+ жалобы одного типа → `salon.needs_review = true` автоматически
- [ ] `POST /api/content/report` — жалоба на сообщение/фото
- [ ] Admin endpoints: список репортов, approve/reject

## BE-19: Ban management
- [ ] IP ban: Redis SET с TTL (auto-expire)
- [ ] Email ban: таблица `banned_emails`
- [ ] Phone ban: таблица `banned_phones`
- [ ] `GET /api/admin/bans` — список всех активных банов
- [ ] `DELETE /api/admin/bans/{id}` — снять вручную
- [ ] Weekly cron: email-отчёт admin (статистика банов)

---

# SPRINT 8 — Admin панель (1 неделя)
**Цель:** admin может управлять всем контентом.

## FE-13: Admin UI
- [ ] `/admin` — отдельный layout (role: admin проверка)
- [ ] `/admin/salons` — список + поиск + статусы + кнопки (verify, deactivate, needs_review)
- [ ] `/admin/professionals` — список + approve/reject новых
- [ ] `/admin/claims` — очередь claiming requests
- [ ] `/admin/moderation` — очередь флагов (текст/фото) + Approve/Reject
- [ ] `/admin/reports` — жалобы на салоны + actions (mark closed, update data, dismiss)
- [ ] `/admin/users` — список + деактивация + ban
- [ ] `/admin/bans` — активные баны + ручное снятие
- [ ] `/admin/translations` — статус переводов (сколько переведено, очередь)
- [ ] `/admin/stats` — дашборд: салоны/мастера/записи/новые пользователи/доход

---

# SPRINT 9 — Монетизация (2 недели)
**Цель:** первые платящие клиенты.

## BE-20: Stripe интеграция
- [ ] Stripe SDK, конфиг в env
- [ ] Seeder: заполнить `subscription_plans` (Free/Pro/Business/MasterPro)
- [ ] `POST /api/payments/subscribe` — создать Stripe Checkout Session
- [ ] `POST /api/payments/webhook` — обработка событий:
  - `checkout.session.completed` → activate subscription
  - `customer.subscription.deleted` → deactivate
  - `invoice.payment_failed` → notify owner
- [ ] `GET /api/payments/portal` → Stripe Customer Portal (управление картой, отмена)
- [ ] Feature gate middleware: `require_plan('pro')` — 402 если нет активной подписки
- [ ] 14-дневный триал при первом claiming

## BE-21: Payment provider abstraction
- [ ] `PaymentProvider` ABC в `app/services/payments/base.py`
- [ ] `StripeProvider` реализация
- [ ] `NOWPaymentsProvider` stub (пустой, для будущей крипты)
- [ ] Конфиг: `PAYMENT_PROVIDER=stripe` → DI container выбирает нужный

## FE-14: Pricing + Billing UI
- [ ] `/[locale]/pricing` — страница тарифов (сравнительная таблица)
- [ ] Stripe Checkout — редирект
- [ ] Возврат после оплаты → `/dashboard?subscribed=true` + success banner
- [ ] `/[locale]/dashboard/billing` — текущий тариф + Stripe Portal ссылка
- [ ] Feature lock UI: если нет подписки → overlay «Доступно в Pro»

---

# SPRINT 10 — Мобильное приложение (3 недели)
**Цель:** iOS + Android в App Store / Play Store.

## MOB-01: Expo проект
- [ ] `npx create-expo-app mobile --template` в `/root/beauty-gr/mobile/`
- [ ] Expo Router + NativeWind + TanStack Query
- [ ] Общий API клиент с frontend (`lib/api.ts` → shared или copy)
- [ ] Конфиг: `app.json` (name: Lookla, bundle IDs, icons)

## MOB-02: Основные экраны
- [ ] Onboarding: выбор языка (4 флага)
- [ ] Поиск: строка + фильтры + список результатов
- [ ] Карта: react-native-maps + маркеры + bottom sheet
  - Тап на маркер → карточка → «Открыть профиль»
- [ ] Профиль салона: фото/галерея + контакты + кнопки
- [ ] Профиль мастера: портфолио + расписание
- [ ] Auth: Login / Register / OAuth экраны

## MOB-03: Booking + Account
- [ ] Booking flow (5 шагов, as per Sprint 5)
- [ ] «Мои записи» экран + отмена
- [ ] Сообщения (список тредов + тред)
- [ ] Настройки (язык, уведомления, профиль)

## MOB-04: Push уведомления
- [ ] Expo Push + FCM (Android) + APNs (iOS)
- [ ] Backend: `POST /api/account/push-token` — сохранить device token
- [ ] Уведомления: новое сообщение, подтверждение записи, напоминание

## MOB-05: Публикация
- [ ] EAS Build: iOS `.ipa` + Android `.aab`
- [ ] Google Play: $25 регистрация → TestFlight → Prod
- [ ] App Store: $99/год Apple Developer → TestFlight → Review → Prod

---

# SPRINT 11 — AI Ассистент (2 недели)
**Цель:** чат-бот внутри приложения помогает найти и записаться.

## BE-22: AI Chat API
- [ ] `POST /api/assistant/chat` — принять сообщение, вернуть ответ
  - История разговора в Redis (TTL 30 мин)
  - Авто-определение языка → ответ на том же языке
- [ ] Function calling tools:
  - `search_salons(city, service, max_price, near_lat, near_lng)`
  - `get_salon_details(salon_id)`
  - `check_availability(salon_id, service_id, date_range)`
  - `create_booking(...)` — создаёт pending, требует подтверждения
  - `get_my_bookings(user_id)`
  - `send_availability_request(salon_id, notes)`
- [ ] Системный промпт из `DOCS/AI_SYSTEM_PROMPT.md` (обновляется при изменениях)
- [ ] Модель: `gpt-4o-mini` или `claude-haiku-4-5` (дешевле всего)
- [ ] Cost guard: max 20 turns/conversation, max 50 conversations/user/day

## FE-15: Chat bubble
- [ ] Floating chat button (bottom-right) на всех страницах
- [ ] Chat panel (sidebar/modal): typing indicator, messages, suggested queries
- [ ] В mobile: отдельный экран «Ассистент»

## DOC-01: AI System Prompt
- [ ] Создать `DOCS/AI_SYSTEM_PROMPT.md` — описание платформы для AI
  - Что умеет делать (функции)
  - Tone of voice (дружелюбный, профессиональный)
  - Ограничения (не давать мед. советы, не обещать цены которые могут измениться)
  - Примеры Q&A на всех 4 языках

---

# SPRINT 12 — SEO + Growth (параллельно 8-11)
**Цель:** органический трафик.

## SEO-01
- [ ] Автогенерация `/[locale]/[city]/[category]` страниц (SSG)
  - Например: `/el/athens/nails` → «Μανικιούρ στην Αθήνα - 87 σαλόνια»
  - Около 500+ страниц (15 городов × 10 категорий × 4 языка)
- [ ] FAQ компонент + Schema.org FAQPage на категорийных страницах
- [ ] Breadcrumbs + Schema.org BreadcrumbList
- [ ] Internal linking: каждая категория ссылается на топ-5 салонов
- [ ] Open Graph preview cards (og:image генерация через Edge Runtime)
- [ ] Canonical URLs для всех страниц

## SEO-02: Content
- [ ] Blog section `/[locale]/blog` (MDX файлы, без CMS для старта)
  - Статьи: «Лучшие nail мастера Афин 2026», «Как выбрать парикмахера» и т.д.
  - 2-4 статьи для старта на греческом + английском
- [ ] Google Business Profile: инструкция для владельцев из дашборда

---

# SPRINT 13 — DevOps + Мониторинг (параллельно всему)

## OPS-01: Бэкапы
- [ ] `/opt/backup/beauty_backup.sh` — pg_dump + gzip + rclone → B2
- [ ] cron: `0 3 * * * /opt/backup/beauty_backup.sh`
- [ ] `/opt/backup/test_restore.sh` — тест восстановления
- [ ] cron: `0 4 1 * * /opt/backup/test_restore.sh` — раз в месяц
- [ ] Логи бэкапов → `/opt/backup/logs/`

## OPS-02: Мониторинг
- [ ] Sentry: backend + frontend проект
- [ ] PostHog: analytics (pageviews, events, funnels)
- [ ] UptimeRobot (free): ping `lookla.gr/api/health` каждые 5 мин → email при падении
- [ ] Nginx access log → логгировать 4xx/5xx

## OPS-03: Oracle Cloud
- [ ] Зарегистрировать аккаунт Oracle Cloud (free tier)
- [ ] Создать ARM VM (4 vCPU / 24 GB) — резервный сервер
- [ ] Настроить Docker + docker-compose (идентично production)
- [ ] Настроить rclone sync БД бэкапов
- [ ] Держать «горячим» (синхронизация БД раз в сутки) — готово к migration в 1 день

---

# Workflow разработки

## Git flow
```
main          — production, защищённая ветка
develop       — integration branch
feature/BE-XX — бэкенд задача
feature/FE-XX — фронтенд задача
hotfix/XXX    — срочные фиксы → сразу в main
```

## Процесс задачи
```
1. Открыть задачу из этого файла
2. git checkout -b feature/BE-XX
3. Реализовать
4. Обновить DOCS (API.md, FEATURES.md)
5. Обновить Changelog в CLAUDE.md
6. PR → develop → review → merge
7. Отметить задачу [x] в этом файле
```

## Деплой
```
develop → main → GitHub Actions →
SSH на сервер → git pull → docker compose up -d --build
Zero-downtime: --no-deps --scale (при необходимости)
```

## Тестирование каждого спринта
После каждого спринта — product owner тестирует основной flow.
Баги → hotfix ветка → fast merge.

---

# Зависимости между спринтами

```
Sprint 0 (Foundation)
    ↓
Sprint 1 (DB + API)
    ↓
Sprint 2 (Frontend) ←→ Sprint 3 (Auth) — параллельно
    ↓
Sprint 4 (Business accounts) — требует Sprint 3
    ↓
Sprint 5 (Booking) — требует Sprint 4
Sprint 6 (Chat)    — требует Sprint 3
    ↓
Sprint 7 (Moderation) — требует Sprint 2+3
Sprint 8 (Admin)      — требует Sprint 7
    ↓
Sprint 9 (Payments) — требует Sprint 4+5
    ↓
Sprint 10 (Mobile) — требует Sprint 5+6 (stable API)
Sprint 11 (AI)     — требует Sprint 5 (features)
    ↓
Sprint 12 (SEO) — параллельно с 8-11
Sprint 13 (DevOps) — параллельно с ВСЕМ
```

---

# Временная оценка

| Sprint | Длительность | Кем |
|--------|-------------|-----|
| 0 Foundation | 3 дня | Claude |
| 1 DB + API | 2 недели | Claude |
| 2 Frontend | 2 недели | Claude |
| 3 Auth | 10 дней | Claude |
| 4 Business accounts | 2 недели | Claude |
| 5 Booking | 2.5 недели | Claude |
| 6 Chat | 1.5 недели | Claude |
| 7 Moderation | 1 неделя | Claude |
| 8 Admin | 1 неделя | Claude |
| 9 Payments | 2 недели | Claude |
| 10 Mobile | 3 недели | Claude |
| 11 AI | 2 недели | Claude |
| 12 SEO | параллельно | Claude |
| 13 DevOps | параллельно | Claude |
| **ИТОГО** | **~22 недели** | |

**Первый публичный запуск (MVP):** конец Sprint 2 (~6 недель)
**Первые платящие клиенты:** конец Sprint 9 (~18 недель)
**Полный продукт:** ~22 недели (~5.5 месяцев)
