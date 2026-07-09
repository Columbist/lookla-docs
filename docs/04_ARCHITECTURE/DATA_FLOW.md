---
title: Data Flow
status: Draft
version: 0.1
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 06_ENGINEERING/AUDIT.md
  - 04_ARCHITECTURE/FEATURE_FLAGS.md
  - 01_PRODUCT/PRODUCT_TERMINOLOGY.md
implementation_status: Described from audit — pending formal approval
---

# Data Flow
**Lookla Beauty Marketplace**

> **DRAFT — describes current implementation from the Engineering Audit.**  
> Must be formally approved before it is used as a reference for new feature design.

---

## Purpose

This document describes how data moves through the Lookla platform: from external sources, through the database, to the user.

---

## Current Data Flow (from Engineering Audit)

### Inbound: Aggregated Data

```
External sources (Google Places, Vrisko, XO, BeautyProject, Treatwell)
        ↓
Crawler (Celery worker, 2 concurrency, 500MB cap)
        ↓
PostgreSQL 16 (primary, single instance)
```

Crawlers run on schedule: Vrisko (Tue), XO (Tue), BeautyProject (Wed), Treatwell (Thu).  
Google Places crawler is disabled (cost incident, July 2026).

---

### Read: Client Discovery

```
User browser → Nginx → Next.js (SSR or CSR)
                         ↓
                    FastAPI (sync, port 8001)
                         ↓
                    PostgreSQL (read)
                         ↓
                    Response → Nginx → Browser
```

Photos: lazy R2 migration. First view of a Google Places URL proxied through `/api/media/photo/{id}`, uploaded to R2, URL updated in DB. Subsequent views served from `cdn.lookla.gr`.

Translation: first real-user view triggers GPT-4o-mini translation batch, result cached in DB. Bot requests return empty (no translation cost).

---

### Auth Flow

```
Login/Register → FastAPI → PostgreSQL (users table)
                         → httpOnly cookies (access: 15min, refresh: 30d)
Google OAuth → FastAPI → JWKS verification → upsert user → cookies
```

---

## Sections Awaiting Approval

_[Formal data flow diagrams, approved architecture decisions — awaiting approval]_

---

*Last updated: 2026-07-09*
