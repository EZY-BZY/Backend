"""Twilio integrations: **Programmable SMS** (custom body + ``From``) and **Verify** (no ``From``).

Owner OTP delivery:

- Default: custom SMS via :func:`send_custom_sms` (needs a **Twilio-owned** ``TWILIO_PHONE_NUMBER``).
- If ``TWILIO_OWNER_USE_VERIFY_FOR_OTP=true`` and Verify is configured: Twilio sends the code (no ``From``
  in the API) — avoids error **21659** when you only have a personal mobile.

See :func:`owner_otp_uses_twilio_verify`.
"""

from __future__ import annotations

import logging

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class SmsSendError(Exception):
    """Raised when Twilio returns an error and the caller asked to surface failures."""


def normalize_e164_phone(phone: str) -> str:
    """Best-effort E.164: strip spaces; ensure leading +."""
    p = phone.strip().replace(" ", "")
    if not p:
        return p
    if p.startswith("+"):
        return p
    return f"+{p}"


def twilio_sms_ready(settings: Settings | None = None) -> bool:
    """True when Programmable SMS can run (AC + token + ``From`` number, and env allows sending)."""
    s = settings or get_settings()
    ac = (s.twilio_account_sid or "").strip()
    token = (s.twilio_auth_token or "").strip()
    from_phone = (s.twilio_phone_number or "").strip()

    if not ac or not token or not from_phone:
        return False

    if ac.upper().startswith("VA"):
        return False

    if s.environment != "production" and not s.twilio_send_sms_in_non_production:
        return False

    return True


def send_custom_sms(
    *,
    to_phone: str,
    message: str,
    raise_on_failure: bool = False,
) -> bool:
    """
    Send a custom SMS via ``Client.messages.create`` (body + ``from_`` Twilio number).

    Returns ``True`` if skipped (not configured) or if Twilio accepted the message.
    Returns ``False`` on Twilio failure when ``raise_on_failure`` is False.
    """
    settings = get_settings()

    if not twilio_sms_ready(settings):
        logger.info(
            "Twilio custom SMS skipped | to=%s | need TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, "
            "TWILIO_PHONE_NUMBER; non-prod needs TWILIO_SEND_SMS_IN_NON_PRODUCTION=true",
            normalize_e164_phone(to_phone),
        )
        return True

    to_e164 = normalize_e164_phone(to_phone)
    from_id = settings.twilio_phone_number.strip()
    ac = (settings.twilio_account_sid or "").strip()

    logger.info(
        "Twilio Messages REQUEST | to=%s | from=%s | body_len=%s",
        to_e164,
        from_id,
        len(message),
    )

    try:
        client = Client(ac, settings.twilio_auth_token)
        sms = client.messages.create(body=message, from_=from_id, to=to_e164)
        logger.info(
            "Twilio custom SMS RESPONSE | sid=%s | status=%s | to=%s",
            sms.sid,
            getattr(sms, "status", None),
            to_e164,
        )
        return True
    except TwilioRestException as e:
        if e.code == 21659:
            logger.error(
                "Twilio 21659: TWILIO_PHONE_NUMBER (%s) is not a Twilio sender on this account. "
                "You cannot use a normal personal mobile as From. Fix: (1) Buy a Twilio number and set "
                "TWILIO_PHONE_NUMBER to it, or (2) Set TWILIO_OWNER_USE_VERIFY_FOR_OTP=true and "
                "TWILIO_VERIFY_SERVICE_SID (VA…) to send OTP via Verify instead (no From).",
                from_id,
            )
        else:
            logger.error(
                "Twilio custom SMS ERROR | code=%s | status=%s | msg=%s | uri=%s",
                e.code,
                e.status,
                e.msg,
                getattr(e, "uri", None),
            )
        if raise_on_failure:
            raise SmsSendError(f"Twilio error {e.code}: {e.msg}") from e
        return False


def owner_otp_uses_twilio_verify(settings: Settings | None = None) -> bool:
    """True when owner OTP should use Verify (Twilio-generated code, no ``From`` number)."""
    s = settings or get_settings()
    return bool(s.twilio_owner_use_verify_for_otp) and twilio_verify_ready(s)


def owner_otp_sms_body(*, otp_code: str, name: str | None = None, app_name: str | None = None) -> str:
    """Friendly SMS for phone verification (ASCII-friendly for GSM segments)."""
    brand = (app_name or "").strip() or "B-easy"
    code = otp_code.strip()
    who = (name or "").strip()
    greeting = f"Hi {who}! " if who else "Hi! "
    return (
        f"{greeting}Thanks for choosing {brand}.\n\n"
        f"Your verification code is: {code}\n\n"
        "Enter it in the app to confirm your number or i will tell your mama "
        "if you didn't sign up, i will find you and fuck you up.\n\n"
        "Glad you're here! love you"
    )


def send_otp_sms(
    *,
    to_phone: str,
    otp_code: str,
    name: str | None = None,
    raise_on_failure: bool = False,
) -> bool:
    """
    Owner registration / resend OTP.

    If :func:`owner_otp_uses_twilio_verify` is true, starts Twilio Verify (``otp_code`` is ignored).
    Otherwise sends :func:`owner_otp_sms_body` via Programmable SMS.
    """
    settings = get_settings()
    if owner_otp_uses_twilio_verify(settings):
        logger.info(
            "Owner OTP delivery: Twilio Verify (TWILIO_OWNER_USE_VERIFY_FOR_OTP); "
            "ignoring app-generated otp for SMS body"
        )
        return start_phone_verification(to_phone=to_phone, raise_on_failure=raise_on_failure)
    body = owner_otp_sms_body(otp_code=otp_code, name=name, app_name=settings.app_name)
    return send_custom_sms(to_phone=to_phone, message=body, raise_on_failure=raise_on_failure)


# --- Twilio Verify (owner OTP when ``TWILIO_OWNER_USE_VERIFY_FOR_OTP`` or standalone helpers) ---


def twilio_verify_ready(settings: Settings | None = None) -> bool:
    """
    True when Verify is fully configured and we may call Twilio (production,
    or non-production with ``TWILIO_SEND_SMS_IN_NON_PRODUCTION``).
    """
    s = settings or get_settings()
    ac = (s.twilio_account_sid or "").strip()
    token = (s.twilio_auth_token or "").strip()
    va = (s.twilio_verify_service_sid or "").strip()
    if not ac or not token or not va:
        return False
    if ac.upper().startswith("VA"):
        return False
    if s.environment != "production" and not s.twilio_send_sms_in_non_production:
        return False
    return True


def _verify_service(settings: Settings):
    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    return client.verify.v2.services(settings.twilio_verify_service_sid)


def start_phone_verification(*, to_phone: str, raise_on_failure: bool = False) -> bool:
    """Start Verify SMS (Twilio-generated code; no ``From`` in API)."""
    settings = get_settings()
    if not twilio_verify_ready(settings):
        logger.info(
            "Twilio Verify skipped | to=%s | need TWILIO_ACCOUNT_SID (AC), TWILIO_AUTH_TOKEN, "
            "TWILIO_VERIFY_SERVICE_SID (VA); non-prod needs TWILIO_SEND_SMS_IN_NON_PRODUCTION=true",
            normalize_e164_phone(to_phone),
        )
        return True

    to_e164 = normalize_e164_phone(to_phone)
    logger.info("Twilio Verify Verifications | to=%s | channel=sms", to_e164)
    try:
        svc = _verify_service(settings)
        v = svc.verifications.create(to=to_e164, channel="sms")
        logger.info(
            "Twilio Verify Verifications RESPONSE | sid=%s | status=%s | valid=%s",
            v.sid,
            getattr(v, "status", None),
            getattr(v, "valid", None),
        )
        return True
    except TwilioRestException as e:
        logger.error(
            "Twilio Verify Verifications ERROR | code=%s | status=%s | msg=%s | uri=%s",
            e.code,
            e.status,
            e.msg,
            getattr(e, "uri", None),
        )
        if raise_on_failure:
            raise SmsSendError(f"Twilio error {e.code}: {e.msg}") from e
        return False


def check_phone_verification(*, to_phone: str, code: str, raise_on_failure: bool = False) -> bool:
    """``VerificationCheck`` with ``To`` + ``Code``; True if status is ``approved``."""
    if not twilio_verify_ready():
        return False

    settings = get_settings()
    to_e164 = normalize_e164_phone(to_phone)
    code_stripped = code.strip()
    logger.info(
        "Twilio Verify VerificationCheck | to=%s | code_len=%s",
        to_e164,
        len(code_stripped),
    )
    try:
        svc = _verify_service(settings)
        c = svc.verification_checks.create(to=to_e164, code=code_stripped)
        ok = c.status == "approved"
        logger.info(
            "Twilio Verify VerificationCheck RESPONSE | status=%s | sid=%s",
            getattr(c, "status", None),
            getattr(c, "sid", None),
        )
        return ok
    except TwilioRestException as e:
        logger.error(
            "Twilio Verify VerificationCheck ERROR | code=%s | status=%s | msg=%s | uri=%s",
            e.code,
            e.status,
            e.msg,
            getattr(e, "uri", None),
        )
        if raise_on_failure:
            raise SmsSendError(f"Twilio error {e.code}: {e.msg}") from e
        return False
