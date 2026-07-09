---
title: Performance Architecture
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 04_ARCHITECTURE/FRONTEND_ARCHITECTURE.md
  - 04_ARCHITECTURE/BACKEND_ARCHITECTURE.md
  - 04_ARCHITECTURE/DATABASE_SCHEMA.md
  - 06_ENGINEERING/AUDIT.md
implementation_status: Describes current performance posture + targets for MVP
---

# Performance Architecture
**Lookla Beauty Marketplace**

> **Approved.** Defines performance targets for MVP launch and documents current implementation's performance characteristics.
>
> Performance work follows the same evidence-first principle (DEC-004): measure first, optimize what hurts. Do not optimize speculatively.

---

## 1. Core Web Vitals Targets (MVP)

Google uses Core Web Vitals as a ranking signal. Lookla's primary SEO surface is the Salon Detail page — it must meet the "Good" threshold.

| Metric | Target | Threshold |
|---|---|---|
| **LCP** (Largest Contentful Paint) | < 2.5s | Good: <2.5s / Needs improvement: 2.5–4s / Poor: >4s |
| **CLS** (Cumulative Layout Shift) | < 0.1 | Good: <0.1 / Needs improvement: 0.1–0.25 / Poor: >0.25 |
| **INP** (Interaction to Next Paint) | < 200ms | Good: <200ms / Needs improvement: 200–500ms / Poor: >500ms |
| **TTFB** (Time to First Byte) | < 800ms | Server response target |

**Measurement:** Google Search Console (post-launch, real user data). PageSpeed Insights (lab data, pre-launch).

**Priority pages for measurement:**
1. `/salons/[slug]` — conversion page; most SEO critical
2. `/search` — discovery page; CSR so Core Web Vitals depend on bundle size
3. `/` (homepage) — entry point

---

## 2. SSR vs CSR: Performance Implications

| Page | Render | LCP source | Risk |
|---|---|---|---|
| Homepage | SSR | Server-rendered HTML | Low — first paint is fast |
| Search | CSR | JS bundle + first API response | Medium — bundle size critical |
| Salon detail | SSR (meta) + CSR (body) | Hero photo (LCP) | Photo load is the bottleneck |
| About, Contact | SSR | Server-rendered HTML | Low |
| Admin | CSR | JS bundle | Not performance-critical (internal) |

**Salon detail critical path:**
```
Browser → Nginx → Next.js SSR (metadata + initial HTML)
  → Browser renders title, placeholder
  → JS bundle loads
  → SalonDetailClient hydrates
  → Hero photo loads from R2 CDN  ← THIS IS LCP
  → IntersectionObserver attaches
  → Services/reviews load when scrolled into view
```

The LCP is the hero photo. Photo load time determines whether the page passes Core Web Vitals.

---

## 3. Image Optimisation

### Current State

- Photos sourced from Google Places (proxy via `/api/media/photo/{id}`) or R2 CDN
- R2 serves via Cloudflare (`cdn.lookla.gr`) — CDN edge caching included
- No explicit resize on lazy R2 migration (full-resolution Google images may be uploaded)

### Required for MVP

**Explicit resizing on R2 upload:**

When a photo is proxied and uploaded to R2, it must be resized to at least two sizes:
- `1200w` — hero/detail view
- `400w` — card thumbnail (SalonCard)
- `800w` — gallery view (optional)

**Format:** WebP preferred (25–35% smaller than JPEG at same quality). JPEG fallback for older browsers.

**Next.js `<Image>` component:**
```tsx
import Image from 'next/image';

<Image
  src={photo.url}
  alt={salon.name}
  width={1200}
  height={800}
  priority={isPrimary}  // priority=true for LCP image (hero photo only)
  sizes="(max-width: 640px) 100vw, (max-width: 1024px) 66vw, 1200px"
/>
```

Using `next/image`:
- Automatically generates `srcset` for responsive sizes
- Adds `loading="lazy"` by default (except `priority=true`)
- Prevents CLS by reserving space via explicit width/height

**Critical:** The hero photo (primary photo on salon detail) must be `priority={true}` — this tells Next.js to preload it, which directly improves LCP.

### Cloudflare Image Resizing (Future)

Cloudflare R2 + Image Resizing can serve images at any size on-demand via URL parameters (`?width=400&format=webp`). This eliminates the need to store multiple sizes. Consider enabling when R2 storage costs become significant.

---

## 4. Pagination and Infinite Scroll

**Search page:** 24 salons per page. Infinite scroll via `IntersectionObserver` sentinel.

**Performance characteristics:**
- First render: loads 24 salons + their photos
- Each scroll load: additional 24 salons
- Map view: loads ALL matching salons (no pagination) — potential issue if result count is high

**Map view limit:** If a search returns 5000+ salons (e.g., unfiltered national search), the map response will be large. For MVP (Athens focus), this is unlikely. For post-MVP national launch, add a map result cap (e.g., 500 pins maximum with a "Zoom in to see more" message).

**Virtualisation:** Not implemented. If a user scrolls through 200+ search results, all rendered SalonCards are in the DOM. For MVP traffic levels, this is acceptable. Add `react-virtual` if scroll performance degrades.

---

## 5. Lazy Loading

Two uses of `IntersectionObserver` in the current implementation:

### Infinite Scroll (Search page)

```typescript
// Sentinel div at bottom of card grid
const observer = new IntersectionObserver((entries) => {
  if (entries[0].isIntersecting && hasMore) {
    loadNextPage();
  }
}, { threshold: 0.1 });
observer.observe(sentinelRef.current);
```

Triggers additional API calls when the user approaches the bottom of results.

### Lazy Section Loading (Salon Detail)

```typescript
// Services and reviews sections
const sectionObserver = new IntersectionObserver((entries) => {
  if (entries[0].isIntersecting) {
    loadSection();
    sectionObserver.disconnect();
  }
}, { threshold: 0.1 });
sectionObserver.observe(sectionRef.current);
```

Triggers lazy API calls for services and reviews when those sections enter the viewport. This is also the bot protection mechanism — bots without JS never trigger these.

**Critical invariant:** Do not change the IntersectionObserver disconnect pattern in the salon detail lazy loader. The `disconnect()` after first trigger ensures the API call happens exactly once, not repeatedly. Removing it would cause repeated API calls on scroll.

---

## 6. Caching Strategy

### CDN Layer (Cloudflare)

| Resource | Cache behaviour | TTL |
|---|---|---|
| R2 photos (`cdn.lookla.gr`) | Cached at Cloudflare edge | Default Cloudflare cache (4 hours for images) |
| Static Next.js assets (`_next/static/`) | Immutable — cached forever | `Cache-Control: public, max-age=31536000, immutable` |
| HTML pages (SSR) | Not cached at edge | `Cache-Control: no-store` (Next.js default for SSR) |

### Application Layer (Next.js fetch cache)

| Request | Current | Recommended |
|---|---|---|
| SSR: salon detail (GET /api/salons/{id}) | `cache: 'no-store'` | Keep — hours change |
| SSR: categories (GET /api/categories) | `cache: 'no-store'` | Change to `next: { revalidate: 86400 }` |
| SSR: areas (GET /api/areas) | — | Use `next: { revalidate: 86400 }` |
| CSR: search results | `cache: 'no-store'` | Keep — filter-dependent |
| CSR: salon services/reviews | `cache: 'no-store'` | Keep — translated on first view |

### Database Layer

**Translation caching:** Translated service names and review texts are stored in DB columns (`name_ru`, `text_ru`, etc.). Once translated, they are never re-translated. This is the primary cost control mechanism for OpenAI.

**No Redis caching for queries:** Not implemented. Acceptable for MVP traffic. Add when DB query times exceed 100ms on common queries.

---

## 7. Database Query Optimisation

### Search Query Performance

The main search query in `/api/salons` runs:
1. Full-text search on `name || name_el || address_city` via `to_tsvector` + `plainto_tsquery`
2. Category subquery on `services.name ILIKE %keyword%`
3. Batch open/closed check on `salon_hours` for current weekday
4. Batch min-price check on `services.price_from`

**Required indexes (from DATABASE_SCHEMA.md):**

| Index | Type | Query served |
|---|---|---|
| `idx_salons_fts` | GIN on tsvector | Full-text search |
| `idx_salons_address_district` | BTREE | DEC-010 area filter |
| `idx_salons_rating` | BTREE | Default sort |
| `idx_salons_is_active` | BTREE | Filter inactive |
| `idx_salon_hours_salon_id` | BTREE | Open/closed batch |
| `idx_services_salon_id` | BTREE | Min-price batch |
| `idx_services_price_from` | PARTIAL BTREE | Min-price filter |

**GIN index for FTS (verify before launch):**

The audit noted that the GIN index on `to_tsvector` may not be present (created as an expression index on an expression function). Verify with:
```sql
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'salons';
```

If absent, create:
```sql
CREATE INDEX idx_salons_fts ON salons
  USING GIN (to_tsvector('simple', unaccent(
    coalesce(name,'') || ' ' || coalesce(name_el,'') || ' ' || coalesce(address_city,'')
  )));
```

### N+1 Query Pattern

The open/closed and min-price enrichment are batch queries (one query for all returned salons), not N+1. This is correct. Verify the batch patterns are maintained when new fields are added.

### Connection Pooling

SQLAlchemy uses its default pool (`QueuePool`). For MVP load (tens of concurrent users), this is adequate. If connection wait times appear in logs, tune `pool_size` and `max_overflow` in `create_engine()`.

---

## 8. Frontend Bundle Size

**Next.js App Router** code-splits by route automatically. Each page loads only its required JS.

**Leaflet map:** Dynamically imported (`dynamic(() => import('../components/MapView'), { ssr: false })`). Map code is NOT in the main bundle — only loaded when map view is activated. Correct.

**Current risk:** `SalonDetailClient.tsx` is a large client component. When split into sub-components (see FRONTEND_ARCHITECTURE.md §6), each sub-component can be independently lazy-loaded.

**Measure before optimising:** Run `next build && next analyze` (with `@next/bundle-analyzer`) to see actual bundle sizes before making decisions.

---

## 9. Translation Performance

**Current flow (synchronous, blocks request thread):**

```
GET /api/salons/{id}/services?lang=ru
  → Check name_ru IS NULL
  → POST to OpenAI gpt-4o-mini (batch of N service names)
  → Wait 1–3 seconds
  → UPDATE services SET name_ru = ...
  → Return response
```

**Impact:** First-view requests for untranslated content have 1–3s latency. Subsequent requests return instantly from DB cache.

**MVP acceptability:** Acceptable. Only first real user per locale per salon pays the translation cost. After that, it's instant.

**Post-MVP improvement:** Move translation to a Celery background task. Return placeholder ("Loading translation...") immediately. Frontend polls or uses WebSocket to receive translated content. This requires frontend changes and is not needed for MVP traffic levels.

---

## 10. Server Resource Limits

**Current Docker Compose limits:**

| Service | Memory limit | CPU |
|---|---|---|
| `api` | 200 MB | (not set) |
| `web` | 300 MB | (not set) |
| `db` | (not set) | (not set) |
| `redis` | (not set) | (not set) |
| `crawler` | 500 MB | (not set) |

**Risk:** Next.js production build + hot paths may consume >300MB under concurrent load. Monitor with `docker stats` after launch.

**If OOM occurs:**
1. First: increase `web` limit to 512 MB (check available server RAM)
2. If insufficient: split heavy pages into smaller components (reduces SSR memory per request)
3. Do not scale horizontally until vertical scaling is exhausted

**API memory:** 200 MB is tight for synchronous GPT calls (each call may allocate response buffer). If OOM occurs on API during translation: increase limit or move translation to Celery worker.

---

## 11. Performance Checklist (Pre-MVP)

- [ ] Verify GIN index on `salons` FTS tsvector exists
- [ ] Add `idx_salons_address_district` index for DEC-010 area filter
- [ ] Confirm `next/image` `priority={true}` on hero photo (salon detail)
- [ ] Confirm hero photo is served from R2 CDN (`cdn.lookla.gr`) not Google Places URL
- [ ] Run PageSpeed Insights on production salon detail page; target LCP < 2.5s
- [ ] Check `docker stats` under simulated load; verify no OOM
- [ ] Set `next: { revalidate: 86400 }` on categories and areas API calls in SSR pages

---

*Last updated: 2026-07-09*
