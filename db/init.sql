-- Beauty Salon Marketplace — PostgreSQL Schema
-- Greece-focused, multi-source crawler + marketplace

DO $$ BEGIN
    CREATE EXTENSION IF NOT EXISTS postgis;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'postgis not available, skipping (geo queries will use lat/lng columns directly)';
END $$;
CREATE EXTENSION IF NOT EXISTS unaccent;   -- Greek text search

-- ─────────────────────────────────────────────────────────────────────────────
-- LOOKUP TABLES
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE service_categories (
    id          SERIAL PRIMARY KEY,
    slug        VARCHAR(80)  NOT NULL UNIQUE,
    name_en     VARCHAR(120) NOT NULL,
    name_el     VARCHAR(120),                 -- Greek name
    parent_id   INT REFERENCES service_categories(id),
    icon        VARCHAR(80),
    sort_order  INT DEFAULT 0
);

-- Top-level categories + subcategories
INSERT INTO service_categories (slug, name_en, name_el, sort_order) VALUES
  ('hair',            'Hair',              'Μαλλιά',          1),
  ('nails',           'Nails',             'Νύχια',           2),
  ('skin',            'Skin & Face',       'Πρόσωπο & Δέρμα', 3),
  ('waxing',          'Waxing & Threading','Αποτρίχωση',      4),
  ('lashes_brows',    'Lashes & Brows',    'Βλεφαρίδες & Φρύδια', 5),
  ('makeup',          'Makeup',            'Μακιγιάζ',        6),
  ('massage',         'Massage & Body',    'Μασάζ & Σώμα',    7),
  ('barbershop',      'Barbershop',        'Barbershop',       8),
  ('tattoo_piercing', 'Tattoo & Piercing', 'Τατουάζ',         9),
  ('spa',             'Spa & Wellness',    'Spa & Wellness',   10);

-- Hair subcategories
INSERT INTO service_categories (slug, name_en, name_el, parent_id) VALUES
  ('hair_cut',        'Haircut',          'Κούρεμα',      (SELECT id FROM service_categories WHERE slug='hair')),
  ('hair_color',      'Hair Color',       'Βαφή',         (SELECT id FROM service_categories WHERE slug='hair')),
  ('hair_highlights', 'Highlights/Balayage','Ανταύγειες', (SELECT id FROM service_categories WHERE slug='hair')),
  ('hair_treatment',  'Hair Treatment',   'Θεραπεία',     (SELECT id FROM service_categories WHERE slug='hair')),
  ('hair_styling',    'Styling & Blowdry','Χτένισμα',     (SELECT id FROM service_categories WHERE slug='hair')),
  ('hair_extensions', 'Extensions',       'Εξτένσιον',    (SELECT id FROM service_categories WHERE slug='hair'));

-- Nails subcategories
INSERT INTO service_categories (slug, name_en, name_el, parent_id) VALUES
  ('manicure',        'Manicure',         'Μανικιούρ',    (SELECT id FROM service_categories WHERE slug='nails')),
  ('pedicure',        'Pedicure',         'Πεντικιούρ',   (SELECT id FROM service_categories WHERE slug='nails')),
  ('gel_nails',       'Gel Nails',        'Gel Νύχια',    (SELECT id FROM service_categories WHERE slug='nails')),
  ('acrylic_nails',   'Acrylic Nails',    'Ακρυλικά',     (SELECT id FROM service_categories WHERE slug='nails')),
  ('nail_art',        'Nail Art',         'Nail Art',     (SELECT id FROM service_categories WHERE slug='nails'));

-- ─────────────────────────────────────────────────────────────────────────────
-- SALONS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE salons (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    name_el         VARCHAR(255),               -- Greek name if different
    slug            VARCHAR(300) UNIQUE,        -- URL-friendly identifier
    description     TEXT,
    description_el  TEXT,

    -- Location
    address_street  VARCHAR(255),
    address_number  VARCHAR(30),
    address_city    VARCHAR(120),
    address_region  VARCHAR(120),               -- nomos / periphereia
    address_postal  VARCHAR(20),
    address_full    TEXT,                       -- raw address string from source
    lat             DOUBLE PRECISION,
    lng             DOUBLE PRECISION,
    google_place_id VARCHAR(100) UNIQUE,

    -- Contact
    phone_primary   VARCHAR(30),
    phone_secondary VARCHAR(30),
    email           VARCHAR(255),
    website         VARCHAR(500),

    -- Meta
    rating_google   NUMERIC(3,2),               -- 1.00–5.00
    rating_count    INT DEFAULT 0,
    price_level     SMALLINT,                   -- 1=budget, 2=mid, 3=premium (Google scale)
    is_verified     BOOLEAN DEFAULT FALSE,      -- claimed by owner
    is_active       BOOLEAN DEFAULT TRUE,

    -- ── Data freshness ──────────────────────────────────────────────────────
    -- Granular timestamps: each section tracks when it was last confirmed current.
    -- contact_verified_at: phone / email / website checked
    -- hours_verified_at:   opening hours confirmed
    -- services_verified_at: service list + prices refreshed
    -- photos_verified_at:  photo URLs still live
    -- data_verified_at:    any of the above (max of all section stamps) — used for
    --                      the "Updated X days ago" badge shown to end users.
    contact_verified_at  TIMESTAMPTZ,
    hours_verified_at    TIMESTAMPTZ,
    services_verified_at TIMESTAMPTZ,
    photos_verified_at   TIMESTAMPTZ,
    data_verified_at     TIMESTAMPTZ,           -- max(all *_verified_at), auto-maintained
    last_source          VARCHAR(80),           -- which spider last updated this record

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-update data_verified_at = greatest of all section timestamps
CREATE OR REPLACE FUNCTION sync_data_verified_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.data_verified_at := GREATEST(
        NEW.contact_verified_at,
        NEW.hours_verified_at,
        NEW.services_verified_at,
        NEW.photos_verified_at
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_salons_freshness
  BEFORE INSERT OR UPDATE ON salons
  FOR EACH ROW EXECUTE FUNCTION sync_data_verified_at();

CREATE INDEX idx_salons_city        ON salons(address_city);
CREATE INDEX idx_salons_latLng      ON salons(lat, lng);
CREATE INDEX idx_salons_active      ON salons(is_active);
CREATE INDEX idx_salons_verified_at ON salons(data_verified_at);
-- Full-text search (simple tokenizer, works without unaccent extension)
CREATE INDEX idx_salons_fts ON salons
    USING gin(to_tsvector('simple', coalesce(name,'') || ' ' || coalesce(name_el,'') || ' ' || coalesce(address_city,'')));


-- ─────────────────────────────────────────────────────────────────────────────
-- BUSINESS HOURS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE salon_hours (
    id          SERIAL PRIMARY KEY,
    salon_id    INT NOT NULL REFERENCES salons(id) ON DELETE CASCADE,
    day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6), -- 0=Mon, 6=Sun
    open_time   TIME,
    close_time  TIME,
    is_closed   BOOLEAN DEFAULT FALSE,
    UNIQUE (salon_id, day_of_week)
);


-- ─────────────────────────────────────────────────────────────────────────────
-- SERVICES
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE services (
    id              SERIAL PRIMARY KEY,
    salon_id        INT NOT NULL REFERENCES salons(id) ON DELETE CASCADE,
    category_id     INT REFERENCES service_categories(id),
    name            VARCHAR(255) NOT NULL,
    name_el         VARCHAR(255),
    description     TEXT,
    duration_min    INT,                        -- minutes
    price_from      NUMERIC(10,2),
    price_to        NUMERIC(10,2),
    currency        CHAR(3) DEFAULT 'EUR',
    is_active       BOOLEAN DEFAULT TRUE,
    source          VARCHAR(80),                -- 'treatwell', 'google', 'manual'
    source_id       VARCHAR(255)                -- original ID in source system
);

CREATE INDEX idx_services_salon    ON services(salon_id);
CREATE INDEX idx_services_category ON services(category_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- STAFF
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE staff (
    id          SERIAL PRIMARY KEY,
    salon_id    INT NOT NULL REFERENCES salons(id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    bio         TEXT,
    role        VARCHAR(120),                   -- 'hairdresser', 'nail technician', etc.
    photo_url   VARCHAR(500),
    source      VARCHAR(80),
    source_id   VARCHAR(255),
    is_active   BOOLEAN DEFAULT TRUE
);


-- ─────────────────────────────────────────────────────────────────────────────
-- PHOTOS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE photos (
    id          SERIAL PRIMARY KEY,
    salon_id    INT NOT NULL REFERENCES salons(id) ON DELETE CASCADE,
    url         VARCHAR(1000) NOT NULL,
    caption     VARCHAR(255),
    is_primary  BOOLEAN DEFAULT FALSE,
    source      VARCHAR(80),                    -- 'google', 'treatwell', 'facebook'
    width       INT,
    height      INT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_photos_salon ON photos(salon_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- REVIEWS (aggregated from sources, not user-generated yet)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE reviews (
    id              SERIAL PRIMARY KEY,
    salon_id        INT NOT NULL REFERENCES salons(id) ON DELETE CASCADE,
    source          VARCHAR(80) NOT NULL,       -- 'google', 'treatwell', 'facebook'
    source_id       VARCHAR(255),
    author_name     VARCHAR(255),
    rating          SMALLINT CHECK (rating BETWEEN 1 AND 5),
    text            TEXT,
    published_at    DATE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (source, source_id)
);

CREATE INDEX idx_reviews_salon ON reviews(salon_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- SOCIAL LINKS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE social_links (
    id          SERIAL PRIMARY KEY,
    salon_id    INT NOT NULL REFERENCES salons(id) ON DELETE CASCADE,
    platform    VARCHAR(50) NOT NULL,           -- 'instagram', 'facebook', 'tiktok'
    url         VARCHAR(500) NOT NULL,
    UNIQUE (salon_id, platform)
);


-- ─────────────────────────────────────────────────────────────────────────────
-- AMENITIES / TAGS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE tags (
    id      SERIAL PRIMARY KEY,
    slug    VARCHAR(80) UNIQUE NOT NULL,
    name_en VARCHAR(120) NOT NULL,
    name_el VARCHAR(120)
);

INSERT INTO tags (slug, name_en, name_el) VALUES
  ('parking',       'Parking',          'Πάρκινγκ'),
  ('wifi',          'Free Wi-Fi',       'Wi-Fi'),
  ('credit_cards',  'Card Payments',    'Κάρτες'),
  ('accessible',    'Wheelchair Access','Πρόσβαση ΑΜΕΑ'),
  ('kids_friendly', 'Kids Friendly',    'Κατάλληλο για παιδιά'),
  ('private_rooms', 'Private Rooms',    'Ιδιωτικοί χώροι'),
  ('walk_in',       'Walk-in Welcome',  'Χωρίς ραντεβού');

CREATE TABLE salon_tags (
    salon_id INT REFERENCES salons(id) ON DELETE CASCADE,
    tag_id   INT REFERENCES tags(id)   ON DELETE CASCADE,
    PRIMARY KEY (salon_id, tag_id)
);


-- ─────────────────────────────────────────────────────────────────────────────
-- SALON ↔ SERVICE CATEGORY mapping (which categories a salon offers)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE salon_categories (
    salon_id    INT REFERENCES salons(id)             ON DELETE CASCADE,
    category_id INT REFERENCES service_categories(id) ON DELETE CASCADE,
    PRIMARY KEY (salon_id, category_id)
);


-- ─────────────────────────────────────────────────────────────────────────────
-- CRAWLER TRACKING
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE crawler_sources (
    id              SERIAL PRIMARY KEY,
    salon_id        INT REFERENCES salons(id) ON DELETE SET NULL,
    source          VARCHAR(80) NOT NULL,       -- 'google_places', 'treatwell', 'vrisko', 'xo'
    source_id       VARCHAR(255),               -- ID in that source system
    source_url      VARCHAR(1000),
    last_crawled_at TIMESTAMPTZ,
    crawl_status    VARCHAR(30) DEFAULT 'pending', -- pending/success/failed/skipped
    error_message   TEXT,
    raw_data        JSONB,                      -- full raw payload for re-processing
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (source, source_id)
);

CREATE INDEX idx_crawler_source       ON crawler_sources(source);
CREATE INDEX idx_crawler_status       ON crawler_sources(crawl_status);
CREATE INDEX idx_crawler_last_crawled ON crawler_sources(last_crawled_at);
CREATE INDEX idx_crawler_salon        ON crawler_sources(salon_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- USERS (phase 2 — placeholder)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255),
    name            VARCHAR(255),
    phone           VARCHAR(30),
    role            VARCHAR(30) DEFAULT 'user',  -- 'user', 'salon_owner', 'admin'
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Salon ownership link (one user can own multiple salons)
CREATE TABLE salon_owners (
    user_id     INT REFERENCES users(id)   ON DELETE CASCADE,
    salon_id    INT REFERENCES salons(id)  ON DELETE CASCADE,
    PRIMARY KEY (user_id, salon_id)
);

-- Trigger: auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_salons_updated_at
  BEFORE UPDATE ON salons
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_crawler_updated_at
  BEFORE UPDATE ON crawler_sources
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ─────────────────────────────────────────────────────────────────────────────
-- AUTH & SECURITY
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE refresh_tokens (
    id          SERIAL PRIMARY KEY,
    user_id     INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(64) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    revoked_at  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE email_verifications (
    id          SERIAL PRIMARY KEY,
    user_id     INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token       VARCHAR(64) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE password_resets (
    id          SERIAL PRIMARY KEY,
    user_id     INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token       VARCHAR(64) NOT NULL UNIQUE,
    channel     VARCHAR(20) DEFAULT 'email',
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ip_bans (
    id          SERIAL PRIMARY KEY,
    ip          VARCHAR(45) NOT NULL UNIQUE,
    reason      VARCHAR(100),
    expires_at  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE email_bans (
    email       VARCHAR(255) PRIMARY KEY,
    reason      VARCHAR(100),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE blocked_email_domains (
    domain      VARCHAR(255) PRIMARY KEY,
    added_at    TIMESTAMPTZ DEFAULT NOW()
);


-- ─────────────────────────────────────────────────────────────────────────────
-- CLAIMING
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE claiming_tokens (
    id          SERIAL PRIMARY KEY,
    user_id     INT NOT NULL REFERENCES users(id),
    salon_id    INT NOT NULL REFERENCES salons(id),
    token       VARCHAR(10) NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, salon_id)
);


-- ─────────────────────────────────────────────────────────────────────────────
-- PROFESSIONALS (freelance masters)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE professionals (
    id                 SERIAL PRIMARY KEY,
    user_id            INT REFERENCES users(id),
    name               VARCHAR(255) NOT NULL,
    slug               VARCHAR(300) UNIQUE,
    specialty          VARCHAR(120),
    bio                TEXT,
    bio_el             TEXT,
    bio_ru             TEXT,
    bio_uk             TEXT,
    phone              VARCHAR(30),
    instagram          VARCHAR(100),
    email              VARCHAR(255),
    base_city          VARCHAR(120),
    base_lat           DOUBLE PRECISION,
    base_lng           DOUBLE PRECISION,
    service_radius_km  INT DEFAULT 15,
    does_home_visits   BOOLEAN DEFAULT TRUE,
    has_home_studio    BOOLEAN DEFAULT FALSE,
    rating_avg         NUMERIC(3,2),
    review_count       INT DEFAULT 0,
    price_level        SMALLINT,
    is_verified        BOOLEAN DEFAULT FALSE,
    is_active          BOOLEAN DEFAULT TRUE,
    needs_review       BOOLEAN DEFAULT FALSE,
    created_at         TIMESTAMPTZ DEFAULT NOW(),
    updated_at         TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_pros_city ON professionals(base_city);
CREATE INDEX idx_pros_geo  ON professionals(base_lat, base_lng);

CREATE TRIGGER trg_professionals_updated_at
  BEFORE UPDATE ON professionals
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TABLE professional_availability (
    id               SERIAL PRIMARY KEY,
    professional_id  INT NOT NULL REFERENCES professionals(id) ON DELETE CASCADE,
    day_of_week      SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time       TIME,
    end_time         TIME,
    is_available     BOOLEAN DEFAULT TRUE,
    UNIQUE (professional_id, day_of_week)
);

CREATE TABLE professional_portfolio (
    id               SERIAL PRIMARY KEY,
    professional_id  INT NOT NULL REFERENCES professionals(id) ON DELETE CASCADE,
    url_after        VARCHAR(1000) NOT NULL,
    url_before       VARCHAR(1000),
    caption          VARCHAR(255),
    service_tag      VARCHAR(80),
    is_featured      BOOLEAN DEFAULT FALSE,
    sort_order       INT DEFAULT 0,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_portfolio_pro ON professional_portfolio(professional_id);

CREATE TABLE professional_social_links (
    id               SERIAL PRIMARY KEY,
    professional_id  INT NOT NULL REFERENCES professionals(id) ON DELETE CASCADE,
    platform         VARCHAR(50) NOT NULL,
    url              VARCHAR(500) NOT NULL,
    UNIQUE (professional_id, platform)
);


-- ─────────────────────────────────────────────────────────────────────────────
-- STAFF SCHEDULES
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE staff_schedules (
    id           SERIAL PRIMARY KEY,
    staff_id     INT NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    day_of_week  SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time   TIME,
    end_time     TIME,
    is_available BOOLEAN DEFAULT TRUE,
    valid_from   DATE,
    valid_to     DATE,
    UNIQUE (staff_id, day_of_week)
);


-- ─────────────────────────────────────────────────────────────────────────────
-- SUBSCRIPTIONS & PAYMENTS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE subscription_plans (
    id               SERIAL PRIMARY KEY,
    slug             VARCHAR(50) NOT NULL UNIQUE,
    name             VARCHAR(100) NOT NULL,
    target           VARCHAR(20) NOT NULL CHECK (target IN ('salon','professional')),
    price_eur        NUMERIC(8,2) NOT NULL,
    stripe_price_id  VARCHAR(100),
    features         JSONB DEFAULT '[]',
    is_active        BOOLEAN DEFAULT TRUE,
    trial_days       INT DEFAULT 14
);

INSERT INTO subscription_plans (slug, name, target, price_eur, features) VALUES
  ('salon_free',  'Free',       'salon',        0.00, '["directory_listing","basic_profile"]'),
  ('salon_basic', 'Basic',      'salon',       19.00, '["directory_listing","full_profile","booking","chat","analytics_basic"]'),
  ('salon_pro',   'Pro',        'salon',       49.00, '["directory_listing","full_profile","booking","chat","analytics_full","priority_placement","api_access"]'),
  ('pro_free',    'Free',       'professional', 0.00, '["directory_listing","basic_profile"]'),
  ('pro_basic',   'Basic',      'professional',14.00, '["directory_listing","full_profile","booking","portfolio"]'),
  ('pro_pro',     'Pro',        'professional',29.00, '["directory_listing","full_profile","booking","portfolio","analytics","priority_placement"]');

CREATE TABLE salon_subscriptions (
    id                      SERIAL PRIMARY KEY,
    salon_id                INT REFERENCES salons(id),
    professional_id         INT REFERENCES professionals(id),
    plan_id                 INT NOT NULL REFERENCES subscription_plans(id),
    stripe_subscription_id  VARCHAR(100) UNIQUE,
    stripe_customer_id      VARCHAR(100),
    status                  VARCHAR(30) DEFAULT 'trialing'
                            CHECK (status IN ('trialing','active','past_due','cancelled','expired')),
    trial_ends_at           TIMESTAMPTZ,
    current_period_end      TIMESTAMPTZ,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER trg_subscriptions_updated_at
  BEFORE UPDATE ON salon_subscriptions
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ─────────────────────────────────────────────────────────────────────────────
-- APPOINTMENTS & AVAILABILITY REQUESTS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE appointments (
    id                   SERIAL PRIMARY KEY,
    salon_id             INT REFERENCES salons(id),
    professional_id      INT REFERENCES professionals(id),
    staff_id             INT REFERENCES staff(id),
    client_user_id       INT REFERENCES users(id),
    service_id           INT REFERENCES services(id),
    client_name          VARCHAR(255),
    client_phone         VARCHAR(30),
    client_email         VARCHAR(255),
    starts_at            TIMESTAMPTZ NOT NULL,
    ends_at              TIMESTAMPTZ NOT NULL,
    duration_min         INT,
    status               VARCHAR(30) DEFAULT 'pending'
                         CHECK (status IN ('pending','confirmed','cancelled','completed','no_show')),
    notes                TEXT,
    source               VARCHAR(30) DEFAULT 'web',
    cancellation_reason  TEXT,
    created_at           TIMESTAMPTZ DEFAULT NOW(),
    updated_at           TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_appt_salon  ON appointments(salon_id, starts_at);
CREATE INDEX idx_appt_pro    ON appointments(professional_id, starts_at);
CREATE INDEX idx_appt_client ON appointments(client_user_id);

CREATE TRIGGER trg_appointments_updated_at
  BEFORE UPDATE ON appointments
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TABLE availability_requests (
    id               SERIAL PRIMARY KEY,
    client_user_id   INT REFERENCES users(id),
    client_name      VARCHAR(255),
    client_phone     VARCHAR(30),
    salon_id         INT REFERENCES salons(id),
    professional_id  INT REFERENCES professionals(id),
    service_notes    TEXT,
    preferred_dates  TEXT,
    status           VARCHAR(30) DEFAULT 'pending'
                     CHECK (status IN ('pending','replied','converted','declined')),
    reply_text       TEXT,
    proposed_slot    TIMESTAMPTZ,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER trg_avail_req_updated_at
  BEFORE UPDATE ON availability_requests
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ─────────────────────────────────────────────────────────────────────────────
-- MESSAGING
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE conversations (
    id               SERIAL PRIMARY KEY,
    client_user_id   INT NOT NULL REFERENCES users(id),
    salon_id         INT REFERENCES salons(id),
    professional_id  INT REFERENCES professionals(id),
    last_message_at  TIMESTAMPTZ,
    client_unread    INT DEFAULT 0,
    owner_unread     INT DEFAULT 0,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- Partial unique indexes (one conversation per client per salon/professional)
CREATE UNIQUE INDEX idx_conv_salon ON conversations(client_user_id, salon_id)        WHERE salon_id IS NOT NULL;
CREATE UNIQUE INDEX idx_conv_pro   ON conversations(client_user_id, professional_id) WHERE professional_id IS NOT NULL;

CREATE TABLE messages (
    id               SERIAL PRIMARY KEY,
    conversation_id  INT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_user_id   INT NOT NULL REFERENCES users(id),
    body             TEXT,
    attachment_url   VARCHAR(1000),
    message_type     VARCHAR(20) DEFAULT 'text'
                     CHECK (message_type IN ('text','image','slot_proposal')),
    proposed_slot    TIMESTAMPTZ,
    read_at          TIMESTAMPTZ,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_conv ON messages(conversation_id, created_at DESC);


-- ─────────────────────────────────────────────────────────────────────────────
-- MODERATION & REPORTS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE reports (
    id                SERIAL PRIMARY KEY,
    salon_id          INT REFERENCES salons(id),
    professional_id   INT REFERENCES professionals(id),
    reporter_user_id  INT REFERENCES users(id),
    reporter_ip       VARCHAR(45),
    reason            VARCHAR(50) NOT NULL
                      CHECK (reason IN ('closed','wrong_phone','wrong_address','wrong_hours','duplicate','inappropriate','other')),
    description       TEXT,
    status            VARCHAR(20) DEFAULT 'open'
                      CHECK (status IN ('open','reviewed','resolved','dismissed')),
    resolved_by       INT REFERENCES users(id),
    resolved_at       TIMESTAMPTZ,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_reports_salon ON reports(salon_id, status);

CREATE TABLE moderation_queue (
    id                 SERIAL PRIMARY KEY,
    content_type       VARCHAR(50) NOT NULL,
    content_id         INT NOT NULL,
    content_text       TEXT,
    content_url        VARCHAR(1000),
    submitter_user_id  INT REFERENCES users(id),
    auto_flags         JSONB DEFAULT '{}',
    status             VARCHAR(20) DEFAULT 'pending'
                       CHECK (status IN ('pending','approved','rejected')),
    reviewed_by        INT REFERENCES users(id),
    reviewed_at        TIMESTAMPTZ,
    created_at         TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_modq_status ON moderation_queue(status, created_at);


-- ─────────────────────────────────────────────────────────────────────────────
-- TRANSLATION CACHE
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE translation_cache (
    id               SERIAL PRIMARY KEY,
    text_hash        CHAR(64) NOT NULL UNIQUE,
    source_text      TEXT NOT NULL,
    source_lang      CHAR(2) NOT NULL,
    target_lang      CHAR(2) NOT NULL,
    translated_text  TEXT NOT NULL,
    provider         VARCHAR(30) DEFAULT 'deepl',
    created_at       TIMESTAMPTZ DEFAULT NOW()
);


-- ─────────────────────────────────────────────────────────────────────────────
-- EVENT LOG & WEBHOOKS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE event_log (
    id               BIGSERIAL PRIMARY KEY,
    event_type       VARCHAR(80) NOT NULL,
    payload          JSONB NOT NULL DEFAULT '{}',
    salon_id         INT,
    professional_id  INT,
    user_id          INT,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_evlog_type ON event_log(event_type, created_at DESC);

CREATE TABLE webhooks (
    id             SERIAL PRIMARY KEY,
    owner_user_id  INT REFERENCES users(id),
    salon_id       INT REFERENCES salons(id),
    url            VARCHAR(500) NOT NULL,
    secret         VARCHAR(100) NOT NULL,
    events         TEXT[] NOT NULL DEFAULT '{}',
    is_active      BOOLEAN DEFAULT TRUE,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);
