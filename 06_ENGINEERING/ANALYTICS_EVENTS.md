# GA4 Product Event Specification (T-015)

Status: implemented, pending production verification (DebugView) before T-015 is marked complete. See `IMPLEMENTATION_BACKLOG.md`'s T-015 entry for the completion record once that's done.

This is the single source of truth for Lookla's GA4 product-event catalogue. It is deliberately closed — `trackEvent()` in `frontend/lib/analytics.ts` only accepts these 5 event/parameter combinations, enforced both at compile time (TypeScript overloads) and at runtime (an explicit name allowlist, per-event parameter schemas, and a universal PII denylist). Adding a 6th event means updating this document, the schema in `analytics.ts`, and the test suite in the same change — not just wiring a new `trackEvent()` call somewhere.

## Naming convention

`snake_case`, present-tense verb where applicable (`salon_open`, not `salon_opened`/`SalonOpen`). Matches GA4's own recommended event-naming convention.

## Consent requirement

All 5 events are gated identically: `trackEvent()` no-ops (silently, never throws) unless `window.gtag` already exists (GA already initialized by T-014 — `trackEvent` never triggers initialization itself) **and** `getAnalyticsConsent()` reads `'granted'` from the live `lookla_consent` cookie at the moment of the call. Consent is never cached inside `trackEvent` — a mid-session withdrawal takes effect on the very next call. A call made while consent is absent/rejected/withdrawn is dropped, not queued; there is no replay when consent is later granted.

## Event catalogue

| Event | Trigger | Parameters | Prohibited data | Owner |
|---|---|---|---|---|
| `salon_open` | User opens a salon detail page from a discovery surface (card/marker click, keyboard activation) | `salon_id: string` (numeric DB id), `source: 'search_list'\|'search_map'\|'homepage'\|'masters'`, `locale: 'el'\|'en'\|'ru'\|'uk'` | salon name, phone, address, URL query string, `salon.slug` | `components/SalonCard.tsx` (search_list, homepage, masters); `components/MapView.tsx` (search_map) |
| `contact_action` | Immediately before a phone/WhatsApp/website contact action navigates/deep-links | `salon_id: string`, `channel: 'phone'\|'whatsapp'\|'website'`, `page: 'salon_detail'`, `locale` | phone number, WhatsApp URL, destination website URL/hostname, salon name | `components/ContactButtons.tsx` |
| `search_results_view` | A search/list/map result set finishes loading successfully and the normalized state materially changed | `area: string\|'all'` (canonical slug), `result_count_bucket: '0'\|'1_5'\|'6_20'\|'21_50'\|'51_plus'`, `view: 'list'\|'map'`, `locale` | free-text search query, exact result count, latitude/longitude, map viewport bounds | `app/[locale]/search/page.tsx` |
| `area_select` | User selects a canonical area from the homepage grid or the search filter | `area: string` (canonical slug), `source: 'homepage_grid'\|'search_filter'`, `locale` | arbitrary URL text, the legacy `city` param | `components/AreaGrid.tsx` (homepage_grid); `app/[locale]/search/page.tsx`'s `selectArea()` (search_filter) |
| `language_change` | User explicitly picks a different language from the header or footer switcher | `from_locale`, `to_locale`, `surface: 'header'\|'footer'` | — | `components/LanguageSwitcher.tsx` |

## Allowed values

- `locale`/`from_locale`/`to_locale`: exactly `el`, `en`, `ru`, or `uk` — matches `i18n/request.ts`'s `Locale` type.
- `salon_id`: `String(salon.id)`, the numeric primary key already exposed to the frontend by the API — **never** `salon.slug`. Real slugs observed in production embed the salon's business name (e.g. `harris-anagnostopoulos-12608`), which would make `salon_id` personally identifying if used.
- `area`: a canonical area slug from `/api/areas` (e.g. `athens-center`) or the literal `'all'` (only valid for `search_results_view`, meaning no area filter is active). Never the legacy `city` query param, never arbitrary text.
- `result_count_bucket`: one of 5 fixed buckets (`bucketResultCount()` in `analytics.ts`) — the exact count is never transmitted.
- `channel`, `page`, `source`, `view`, `surface`: fixed closed enums, one value set per event (see table above).

## PII guard design

Two independent layers, both enforced inside `trackEvent()` itself (not left to callers to self-police):

1. **Per-event schema (allowlist).** Each event has an exact set of permitted parameter keys, each with its own validator (numeric-id regex, canonical-slug regex, or closed-enum membership check). `trackEvent` builds its output by iterating the *schema's* keys, not the caller's — any key a caller passes that isn't in the schema is structurally never copied to the payload, valid or not.
2. **Universal denylist (defense-in-depth).** On top of the schema: an explicit `DENIED_PARAM_KEYS` set (email, phone, name, address, message, token, lat/lng, query, URL, cookie, user_id, and related variants) — if *any* of these key names appear anywhere in the caller's raw input object, the entire event is dropped, even though the schema would have ignored them anyway. And every string value, regardless of key, must pass `isSafeGenericValue()`: no whitespace, no `@`, no URL-scheme prefix (`tel:`, `mailto:`, `https://`, etc.), bounded to 64 characters. None of the catalogue's legitimate values (enum tokens, hyphenated slugs, digit strings) ever contain a space, `@`, or scheme prefix — but a name, address, message, email, or destination URL would.

If a value is not a string (an object, array, number, boolean, `null`, `undefined`), the whole event is dropped — this is what makes "the generic API must not accept a nested object" true structurally: nothing but `typeof value === 'string'` ever reaches the schema/denylist checks in the first place.

`trackEvent` never throws — every code path is wrapped in `try/catch`; a broken analytics call cannot break the product.

## Duplicate-prevention strategy

No event in this catalogue uses time-based debounce as its primary guard. Per event:

- **`salon_open`**: exactly one click handler per discovery surface (`SalonCard`'s single wrapping `<Link>`, `MapView`'s single "view" link in the marker preview) — no parent/child nesting exists that could double-fire. The destination page (`SalonDetailClient.tsx`) never calls `trackEvent` itself, so hydration cannot re-fire it.
- **`contact_action`**: three flat, independent `<a>` tags in `ContactButtons.tsx`, none nested inside another trackable element.
- **`search_results_view`**: a `useRef`-held last-tracked normalized-state key (`area|result_count_bucket|view|locale`, built by `buildSearchResultsViewKey()`), compared by exact string equality on every render. Gated on `loading`/`searchError` (list) or `mapLoading`/`mapError` (map) so it never fires mid-load or after a failed API call. A genuinely different state — including one reached via browser back/forward — always fires, since the key changes.
- **`area_select`**: `selectArea()` guards with `if (slug && slug !== area)` before tracking — clearing to "All areas" and reselecting the already-active area are both no-ops for tracking (though navigation still proceeds either way). `AreaGrid`'s homepage click always tracks, since there's no "currently active area" concept on the homepage.
- **`language_change`**: `switchLocale()` guards with `if (locale === currentLocale) return;` before tracking or navigating.

## Cardinality considerations

Every parameter is either a bounded closed enum (≤5 values) or a stable low-cardinality identifier (`salon_id`: bounded by the actual number of salons in the catalogue; `area`: bounded by the number of canonical areas GA4 already knows about). None of the 5 events carry a high-cardinality or unbounded-growth parameter (no raw counts, no free text, no timestamps, no session/user identifiers).

## GA4 Admin — custom dimension checklist (manual, not automated by this change)

T-015 does not register any custom dimension in GA4 — that's a manual Admin-console action, deliberately deferred. Recommended review list once real event volume exists:

- `source` (salon_open, area_select)
- `channel` (contact_action)
- `page` (contact_action — currently always `salon_detail`, so low value until a second page type exists)
- `area` (search_results_view, area_select)
- `result_count_bucket` (search_results_view)
- `view` (search_results_view)
- `locale` / `from_locale` / `to_locale` / `surface` (language_change)

**`salon_id` is explicitly NOT recommended for automatic custom-dimension registration** — consider cardinality (grows with the salon catalogue) and actual reporting needs before registering it; a per-salon custom dimension may not be the right GA4 reporting shape at all (per-salon breakdowns are likely better served by BigQuery export or a different tool once volume justifies it).

## Key events — deferred decision

No event is marked as a GA4 "key event" (formerly "conversion") by this change. Recommendation: `contact_action` is the most plausible candidate for a future key event, matching DEC-017's stated success metric (visitor→contact conversion) — but that decision should wait until real event quality and volume have been validated in production, not be made automatically at launch.

## Known, deliberate gaps

- **`MapView.tsx`'s phone quick-dial button** (in the marker preview card) is **not instrumented**. `contact_action`'s approved contract requires `page: 'salon_detail'`; this button lives on the search/map page, not the salon detail page. Extending the contract to cover it is a candidate for a future ticket, not silently folded into T-015.
- **`masters` page** currently has no salon listings (placeholder/empty state) — `salon_open`'s `'masters'` source value exists in the type contract for forward compatibility but has no live call site yet.
- **City-filtered searches** (`?city=...`, a legacy pre-area filter path) report `area: 'all'` in `search_results_view`, since `city` is not canonical area metadata. This is a known simplification, not a bug.
