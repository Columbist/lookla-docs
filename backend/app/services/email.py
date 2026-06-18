import httpx
from app.core.config import get_settings

settings = get_settings()

TEMPLATES = {
    "verify": {
        "el": ("Επαλήθευση email — Lookla", "Κάντε κλικ για να επαληθεύσετε το email σας: {url}"),
        "en": ("Verify your email — Lookla", "Click to verify your email: {url}"),
        "ru": ("Подтверждение email — Lookla", "Нажмите для подтверждения email: {url}"),
        "uk": ("Підтвердження email — Lookla", "Натисніть для підтвердження email: {url}"),
    },
    "reset": {
        "el": ("Επαναφορά κωδικού — Lookla", "Κωδικός επαναφοράς: {code}  (ισχύει 10 λεπτά)"),
        "en": ("Password reset — Lookla", "Your reset code: {code}  (valid 10 minutes)"),
        "ru": ("Сброс пароля — Lookla", "Ваш код сброса: {code}  (действует 10 минут)"),
        "uk": ("Скидання пароля — Lookla", "Ваш код скидання: {code}  (дійсний 10 хвилин)"),
    },
    "booking_confirm": {
        "el": ("Επιβεβαίωση κράτησης — Lookla", "Η κράτησή σας επιβεβαιώθηκε για {datetime} στο {salon}."),
        "en": ("Booking confirmed — Lookla", "Your booking is confirmed for {datetime} at {salon}."),
        "ru": ("Бронирование подтверждено — Lookla", "Ваша запись подтверждена на {datetime} в {salon}."),
        "uk": ("Бронювання підтверджено — Lookla", "Ваш запис підтверджено на {datetime} у {salon}."),
    },
}


async def send_email(to: str, template: str, lang: str = "el", **kwargs) -> bool:
    if not settings.brevo_api_key:
        print(f"[email] No API key — skipping: {template} to {to}")
        return False

    tmpl = TEMPLATES.get(template, {}).get(lang, TEMPLATES.get(template, {}).get("en"))
    if not tmpl:
        return False

    subject, body_tpl = tmpl
    body = body_tpl.format(**kwargs)

    payload = {
        "sender": {"name": settings.brevo_sender_name, "email": settings.brevo_sender_email},
        "to": [{"email": to}],
        "subject": subject,
        "textContent": body,
    }

    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(
                "https://api.brevo.com/v3/smtp/email",
                json=payload,
                headers={"api-key": settings.brevo_api_key},
                timeout=10,
            )
            return r.status_code in (200, 201)
        except Exception as e:
            print(f"[email] Error: {e}")
            return False
