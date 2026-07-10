# T-003a — FTS GIN Index: Investigation Results

**Date:** 2026-07-10
**Decision:** Verified — Deferred to T-037 (post-MVP)
**Reviewed by:** Product Owner

---

## Database Inventory

### Existing indexes on `salons` (all btree, no GIN)

| Index name | Method | Definition |
|---|---|---|
| `salons_pkey` | btree | `id` |
| `salons_slug_key` | btree | `slug` (unique) |
| `salons_google_place_id_key` | btree | `google_place_id` (unique) |
| `idx_salons_active` | btree | `is_active` |
| `idx_salons_city` | btree | `address_city` |
| `idx_salons_latlng` | btree | `(lat, lng)` |
| `idx_salons_rating_google` | btree | `rating_google DESC NULLS LAST WHERE is_active = true` |
| `idx_salons_verified_at` | btree | `data_verified_at` |
| `ix_salons_address_district` | btree | `address_district` (T-002) |

**GIN index: absent.**

### Schema

- No `tsvector` column on `salons`.
- No generated columns.
- No FTS-maintenance triggers (only `trg_salons_updated_at` and `trg_salons_freshness`).
- `unaccent` extension: installed.

---

## Application FTS Expression

**Only one endpoint uses PostgreSQL FTS:** `GET /api/search` (`backend/app/routers/search.py`, lines 36–38).

```sql
-- WHERE condition (search.py:36-38)
to_tsvector('simple', unaccent(
    coalesce(s.name,'') || ' ' || coalesce(s.name_el,'') || ' ' || coalesce(s.address_city,'')
))
@@
plainto_tsquery('simple', unaccent(:q))
```

**`GET /api/salons`** (the canonical MVP endpoint) uses ILIKE, not FTS.

---

## Function Volatility

```sql
SELECT p.oid::regprocedure, p.provolatile
FROM pg_proc p
WHERE p.proname IN ('unaccent', 'to_tsvector', 'plainto_tsquery');
```

| Function | Volatility | Usable in index expression |
|---|---|---|
| `to_tsvector(regconfig, text)` | **i (IMMUTABLE)** | ✓ Yes |
| `to_tsvector(text)` | s (STABLE) | ✗ No |
| `plainto_tsquery(regconfig, text)` | **i (IMMUTABLE)** | ✓ (query side only) |
| `unaccent(regdictionary, text)` | s (STABLE) | ✗ No |
| `unaccent(text)` | s (STABLE) | ✗ No |

---

## PostgreSQL Rejection

```sql
-- Attempted (diagnostic only, not applied):
CREATE INDEX test_gin ON salons USING GIN (
    to_tsvector('simple', unaccent(coalesce(name,'') || ' ' || coalesce(name_el,'') || ' ' || coalesce(address_city,'')))
);
-- Result:
ERROR:  functions in index expression must be marked IMMUTABLE
```

---

## EXPLAIN Baseline (seq scan, no index)

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT s.id, s.name
FROM salons s
WHERE s.is_active = true
  AND to_tsvector('simple', unaccent(coalesce(s.name,'') || ' ' || coalesce(s.name_el,'') || ' ' || coalesce(s.address_city,'')))
      @@ plainto_tsquery('simple', unaccent('μανικιούρ'))
LIMIT 20;
```

```
Seq Scan on salons s
  Filter: (is_active AND tsvector @@ tsquery)
  Rows Removed by Filter: 3152
  Buffers: shared hit=725
Planning Time:  84.339 ms
Execution Time: 97.790 ms
Rows returned:  20
```

**Note on benchmark interpretation:**
Planning Time (84 ms) dominates due to first-call overhead and catalog cache misses.
Actual filtering time is approximately 13 ms.
The query returned 20 rows after scanning ~3172 rows — moderately selective for this term on 6367 total.
PostgreSQL would reasonably choose seq scan even with an index for an unselective query on a small table.

---

## Alternatives Considered

### Alternative A — Immutable wrapper function
Create `CREATE FUNCTION immutable_unaccent(text) RETURNS text LANGUAGE sql IMMUTABLE STRICT`.

**Rejected because:**
- `IMMUTABLE` is a promise that the function result never changes for the same arguments. `unaccent`'s result depends on the dictionary rules file, which can be changed. Marking the wrapper `IMMUTABLE` creates a hidden maintenance obligation: any unaccent dictionary update requires `REINDEX`.
- PostgreSQL marks `unaccent` as STABLE specifically to avoid this implicit contract. Overriding it with `IMMUTABLE` is technically unsound, not just conservative.
- The endpoint this would serve is deprecated.

### Alternative B — Trigger-maintained `tsvector` column
Add `search_vector tsvector`, a maintenance trigger, a GIN index on the stored column, and update the query.

**Rejected because:**
- Correct long-term architecture, but adds: new column, trigger, backfill migration, GIN index, query change, sync tests.
- All of this serves a deprecated endpoint.
- Better considered as part of T-037 when the canonical endpoint is selected.

### Alternative C — Defer *(selected)*
Accept seq scan. No database change for M-01.

**Rationale:**
- `GET /api/search` is deprecated. The MVP frontend does not use it.
- `GET /api/salons` (canonical MVP endpoint) uses ILIKE and is not helped by a FTS GIN index.
- At 6367 salons and ~13 ms actual scan time, seq scan is acceptable.
- Adding index infrastructure for a deprecated endpoint is technical debt.

---

## Conditions that should trigger T-037

- `GET /api/search` Deprecation header (T-035) has been live for ≥ 30 days with no consumer traffic.
- OR measured search latency under real user traffic exceeds an agreed threshold.
- OR a proposal to add a third search endpoint surfaces (scope freeze signal).
