"""
OTP generation and delivery.

send_otp() is a stub: it logs the code instead of sending an email/SMS.
Swap its body for a real provider (SES, Twilio, etc.) — nothing else in the
request/verify flow needs to change.
"""

import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import OneTimePasscode

logger = logging.getLogger("thinkturf.otp")


def generate_code():
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(settings.OTP_CODE_LENGTH))


def issue_otp(user, channel):
    code = generate_code()
    expires_at = timezone.now() + timedelta(seconds=settings.OTP_TTL_SECONDS)
    otp = OneTimePasscode.objects.create(
        user=user, channel=channel, code=code, expires_at=expires_at
    )
    send_otp(user, channel, code)
    return otp


def send_otp(user, channel, code):
    """Stub delivery. Replace with a real email/SMS provider."""
    destination = user.email if channel == OneTimePasscode.CHANNEL_EMAIL else user.phone
    logger.info("OTP %s for %s via %s to %s", code, user.email, channel, destination)
    print(f"[OTP STUB] {channel} OTP for {user.email}: {code}")
