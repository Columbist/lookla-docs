---
title: Auth Providers
status: Active
version: 1.0
owner: Product Owner (columb@europe.com)
last_updated: 2026-07-09
related_documents:
  - 04_ARCHITECTURE/SECURITY.md
  - 04_ARCHITECTURE/BACKEND_ARCHITECTURE.md
  - 00_GOVERNANCE/DECISION_LOG.md
---

# Auth Providers

## Currently Implemented

### Email / Password (native)
- Registration: `POST /api/auth/register` (requires Cloudflare Turnstile)
- Login: `POST /api/auth/login`
- Token refresh: `GET /api/auth/refresh`
- Logout: `POST /api/auth/logout`
- Password reset: `POST /api/auth/forgot-password` → OTP via email (Resend)
- Email verification: `POST /api/auth/verify-email`

### Google OAuth (RS256 JWKS)
- Route: `GET /api/auth/google` → redirect → `GET /api/auth/google/callback`
- Token validation: RS256 via Google JWKS endpoint (not secret-based)
- Session: same httpOnly JWT cookie as native auth
- Env vars: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`

---

## Post-MVP: Apple Sign In

**Status:** Not implemented. Env vars are present in `.env.example` as placeholders.

**Why deferred:** Apple Sign In requires Apple Developer Program membership, App Store presence, and native SDK integration for iOS. For web-only MVP, Google OAuth covers the use case. Apple Sign In adds implementation complexity (RS256 private key signing for client secret generation, different OIDC flow) with minimal MVP benefit.

**Env vars (do not remove — reserved for Post-MVP):**
```
APPLE_CLIENT_ID=gr.lookla.app   # Bundle ID or Service ID
APPLE_TEAM_ID=                  # 10-char Apple Team ID
APPLE_KEY_ID=                   # Key identifier from Apple Developer
APPLE_PRIVATE_KEY=              # p8 private key (keep secret)
```

**Implementation notes for when this is built:**
- Apple Sign In client secret must be generated as a JWT signed with the p8 private key (expires max 6 months)
- `email` field from Apple ID may be absent on subsequent logins — must store on first login
- Requires `https://` redirect URI registered in Apple Developer console
- Use `python-jose` for JWT signing (already in `requirements.txt`)

**RFC required before implementation:** create `07_RFC/RFC-apple-sign-in.md`.

---

## Not in Roadmap

### Meta WhatsApp Business API
WhatsApp CTAs on salon detail pages use plain `wa.me/{phone}` links — no Meta Business API required. The Meta WhatsApp env vars (`META_WHATSAPP_TOKEN`, `META_PHONE_NUMBER_ID`) were removed from `.env.example` as they had no code usage and are not in the M-01 roadmap.

### Phone OTP / SMS
Not planned. Contact CTAs use direct phone links (`tel:{number}`), not OTP flows.
