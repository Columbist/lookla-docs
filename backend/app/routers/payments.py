"""
Stripe payments: subscriptions for salon owners and professionals.
Pluggable PaymentProvider interface — Stripe is first implementation.
"""
import json
import hashlib
from datetime import datetime, timezone
from typing import Optional
from abc import ABC, abstractmethod

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.config import get_settings
from app.models.user import User

router = APIRouter(prefix="/api/payments", tags=["payments"])
settings = get_settings()


# ─────────────────────────── Abstract Interface ───────────────────────────────

class PaymentSession(BaseModel):
    checkout_url: str
    session_id: str
    provider: str


class PaymentEvent(BaseModel):
    type: str          # subscription.created | subscription.cancelled | payment.failed
    subscription_id: Optional[str] = None
    customer_id: Optional[str] = None
    plan_slug: Optional[str] = None
    raw: dict = {}


class PaymentProvider(ABC):
    @abstractmethod
    async def create_checkout(self, user: User, plan_id: int, success_url: str, cancel_url: str) -> PaymentSession: ...

    @abstractmethod
    async def create_portal(self, customer_id: str, return_url: str) -> str: ...

    @abstractmethod
    async def handle_webhook(self, payload: bytes, signature: str) -> Optional[PaymentEvent]: ...

    @abstractmethod
    async def cancel_subscription(self, subscription_id: str) -> bool: ...


# ─────────────────────────── Stripe Implementation ───────────────────────────

class StripeProvider(PaymentProvider):
    def __init__(self):
        if not settings.stripe_secret_key:
            raise ValueError("STRIPE_SECRET_KEY not configured")
        import stripe
        stripe.api_key = settings.stripe_secret_key
        self._stripe = stripe

    async def create_checkout(self, user: User, plan_id: int, success_url: str, cancel_url: str) -> PaymentSession:
        raise NotImplementedError("Use /api/payments/subscribe directly")

    async def create_portal(self, customer_id: str, return_url: str) -> str:
        session = self._stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return session.url

    async def handle_webhook(self, payload: bytes, signature: str) -> Optional[PaymentEvent]:
        try:
            event = self._stripe.Webhook.construct_event(
                payload, signature, settings.stripe_webhook_secret
            )
        except Exception:
            return None

        e_type = event["type"]
        data = event["data"]["object"]

        if e_type in ("customer.subscription.created", "customer.subscription.updated"):
            return PaymentEvent(
                type="subscription.created",
                subscription_id=data.get("id"),
                customer_id=data.get("customer"),
                raw=dict(data),
            )
        elif e_type == "customer.subscription.deleted":
            return PaymentEvent(
                type="subscription.cancelled",
                subscription_id=data.get("id"),
                customer_id=data.get("customer"),
                raw=dict(data),
            )
        elif e_type == "invoice.payment_failed":
            return PaymentEvent(
                type="payment.failed",
                subscription_id=data.get("subscription"),
                customer_id=data.get("customer"),
                raw=dict(data),
            )
        return None

    async def cancel_subscription(self, subscription_id: str) -> bool:
        try:
            self._stripe.Subscription.cancel(subscription_id)
            return True
        except Exception:
            return False


# ─────────────────────────── Provider factory ─────────────────────────────────

def get_provider() -> Optional[PaymentProvider]:
    provider_name = settings.payment_provider
    if provider_name == "stripe" and settings.stripe_secret_key:
        try:
            return StripeProvider()
        except Exception as e:
            print(f"[payments] Stripe init failed: {e}")
    return None


# ─────────────────────────── Endpoints ───────────────────────────────────────

@router.get("/plans")
def get_plans(db: Session = Depends(get_db)):
    """Public list of subscription plans."""
    rows = db.execute(text("""
        SELECT id, slug, name, target, price_eur, features, trial_days
        FROM subscription_plans WHERE is_active = true ORDER BY price_eur
    """)).mappings().all()
    result = []
    for r in rows:
        d = dict(r)
        if isinstance(d.get("features"), str):
            import json as _json
            d["features"] = _json.loads(d["features"])
        result.append(d)
    return result


@router.post("/subscribe")
async def create_subscription(
    plan_id: int,
    salon_id: Optional[int] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create Stripe Checkout session for a subscription plan."""
    plan = db.execute(text("SELECT * FROM subscription_plans WHERE id = :id AND is_active = true"), {"id": plan_id}).first()
    if not plan:
        raise HTTPException(404, "Plan not found")

    if plan.price_eur == 0:
        # Free plan — just activate it
        _activate_subscription(db, user.id, salon_id, plan_id, None, None, "active")
        return {"status": "ok", "plan": plan.slug}

    provider = get_provider()
    if not provider:
        raise HTTPException(503, "Payment provider not configured")

    base_url = "https://lookla.gr"
    success_url = f"{base_url}/dashboard?subscribed=true&plan={plan.slug}"
    cancel_url = f"{base_url}/pricing"

    try:
        import stripe
        stripe.api_key = settings.stripe_secret_key

        # Get or create Stripe customer
        existing_sub = db.execute(text("""
            SELECT stripe_customer_id FROM salon_subscriptions
            WHERE (salon_id = :sid OR (salon_id IS NULL AND :sid IS NULL))
              AND stripe_customer_id IS NOT NULL
            LIMIT 1
        """), {"sid": salon_id}).first()

        customer_id = existing_sub.stripe_customer_id if existing_sub else None

        if not customer_id:
            customer = stripe.Customer.create(email=user.email, name=user.name or user.email)
            customer_id = customer.id

        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{"price": plan.stripe_price_id, "quantity": 1}] if plan.stripe_price_id else [],
            success_url=success_url + "&session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            subscription_data={"trial_period_days": plan.trial_days or 14},
            metadata={"user_id": user.id, "plan_id": plan_id, "salon_id": salon_id or ""},
        )
        return {"checkout_url": session.url, "session_id": session.id}

    except Exception as e:
        raise HTTPException(500, f"Payment error: {str(e)}")


@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None), db: Session = Depends(get_db)):
    """Handle Stripe webhook events."""
    payload = await request.body()

    provider = get_provider()
    if not provider or not stripe_signature:
        raise HTTPException(400, "Invalid webhook")

    event = await provider.handle_webhook(payload, stripe_signature)
    if not event:
        return {"status": "ignored"}

    if event.type in ("subscription.created",):
        raw = event.raw
        meta = raw.get("metadata", {})
        user_id = int(meta.get("user_id", 0))
        plan_id = int(meta.get("plan_id", 0))
        salon_id = int(meta.get("salon_id")) if meta.get("salon_id") else None
        status = raw.get("status", "active")

        _activate_subscription(db, user_id, salon_id, plan_id,
                                event.subscription_id, event.customer_id, status)

    elif event.type == "subscription.cancelled":
        db.execute(text("""
            UPDATE salon_subscriptions SET status = 'cancelled', updated_at = NOW()
            WHERE stripe_subscription_id = :sid
        """), {"sid": event.subscription_id})
        db.commit()

    elif event.type == "payment.failed":
        db.execute(text("""
            UPDATE salon_subscriptions SET status = 'past_due', updated_at = NOW()
            WHERE stripe_subscription_id = :sid
        """), {"sid": event.subscription_id})
        db.commit()

    return {"status": "ok"}


@router.get("/portal")
async def billing_portal(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Redirect to Stripe Customer Portal."""
    sub = db.execute(text("""
        SELECT ss.stripe_customer_id
        FROM salon_subscriptions ss
        JOIN salon_owners so ON so.salon_id = ss.salon_id
        WHERE so.user_id = :uid
          AND ss.stripe_customer_id IS NOT NULL
        ORDER BY ss.created_at DESC LIMIT 1
    """), {"uid": user.id}).first()

    if not sub:
        raise HTTPException(404, "No active subscription found")

    provider = get_provider()
    if not provider:
        raise HTTPException(503, "Payment provider not configured")

    url = await provider.create_portal(sub.stripe_customer_id, "https://lookla.gr/dashboard")
    return {"portal_url": url}


@router.get("/my-subscription")
def my_subscription(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user's subscription status."""
    # Check via salon ownership
    sub = db.execute(text("""
        SELECT ss.status, ss.trial_ends_at, ss.current_period_end,
               sp.slug AS plan_slug, sp.name AS plan_name, sp.price_eur,
               sp.features
        FROM salon_subscriptions ss
        JOIN subscription_plans sp ON ss.plan_id = sp.id
        JOIN salon_owners so ON ss.salon_id = so.salon_id
        WHERE so.user_id = :uid
        ORDER BY ss.created_at DESC LIMIT 1
    """), {"uid": user.id}).first()

    if not sub:
        # Check professional subscription
        sub = db.execute(text("""
            SELECT ss.status, ss.trial_ends_at, ss.current_period_end,
                   sp.slug AS plan_slug, sp.name AS plan_name, sp.price_eur,
                   sp.features
            FROM salon_subscriptions ss
            JOIN subscription_plans sp ON ss.plan_id = sp.id
            JOIN professionals p ON ss.professional_id = p.id
            WHERE p.user_id = :uid
            ORDER BY ss.created_at DESC LIMIT 1
        """), {"uid": user.id}).first()

    if not sub:
        return {"plan": "free", "status": "active", "features": []}

    return dict(sub)


@router.delete("/cancel")
async def cancel_my_subscription(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Cancel current subscription at period end."""
    sub = db.execute(text("""
        SELECT ss.stripe_subscription_id
        FROM salon_subscriptions ss
        JOIN salon_owners so ON ss.salon_id = so.salon_id
        WHERE so.user_id = :uid AND ss.status IN ('active', 'trialing')
        LIMIT 1
    """), {"uid": user.id}).first()

    if not sub or not sub.stripe_subscription_id:
        raise HTTPException(404, "No active subscription")

    provider = get_provider()
    if provider:
        await provider.cancel_subscription(sub.stripe_subscription_id)

    db.execute(text("""
        UPDATE salon_subscriptions SET status = 'cancelled', updated_at = NOW()
        WHERE stripe_subscription_id = :sid
    """), {"sid": sub.stripe_subscription_id})
    db.commit()
    return {"status": "ok", "message": "Subscription will be cancelled at period end"}


# ─────────────────────────── Helpers ─────────────────────────────────────────

def _activate_subscription(db: Session, user_id: int, salon_id: Optional[int], plan_id: int,
                            stripe_sub_id: Optional[str], stripe_customer_id: Optional[str],
                            status: str):
    if stripe_sub_id:
        db.execute(text("""
            INSERT INTO salon_subscriptions
              (salon_id, plan_id, stripe_subscription_id, stripe_customer_id, status)
            VALUES (:sid, :pid, :sub_id, :cust_id, :status)
            ON CONFLICT (stripe_subscription_id)
            DO UPDATE SET status = :status, updated_at = NOW()
        """), {
            "sid": salon_id, "pid": plan_id,
            "sub_id": stripe_sub_id, "cust_id": stripe_customer_id, "status": status,
        })
    else:
        # Free plan — upsert by salon+plan (no stripe_subscription_id)
        db.execute(text("""
            INSERT INTO salon_subscriptions
              (salon_id, plan_id, stripe_subscription_id, stripe_customer_id, status)
            VALUES (:sid, :pid, NULL, NULL, :status)
            ON CONFLICT (salon_id, plan_id) WHERE stripe_subscription_id IS NULL
            DO UPDATE SET status = :status, updated_at = NOW()
        """), {"sid": salon_id, "pid": plan_id, "status": status})
    db.commit()
