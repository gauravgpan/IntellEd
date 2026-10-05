"""
Session-triggered side effects.

register_reminder() is called from Session.save() — design doc section 5's
"Register reminders" / "Re-register reminders" steps. Sending is a separate
job (apps/scheduling/tasks.py.dispatch_due_reminders), run periodically by
Django-Q2, since nothing in a web request causes a reminder to fire at the
right wall-clock time — that has to come from a scheduler.
"""

import logging
from datetime import timedelta

from django.conf import settings

from .models import Reminder

logger = logging.getLogger("thinkturf.scheduling")


def register_reminder(session):
    """
    Create, or refresh the timing of, the one pending reminder for a
    session. A no-op once that reminder has already been sent or failed —
    rescheduling a session at that point doesn't resurrect an old one.
    """
    send_at = session.starts_at - timedelta(minutes=settings.REMINDER_LEAD_MINUTES)
    reminder, created = Reminder.objects.get_or_create(
        session=session,
        defaults={
            "recipient": session.tutor.user,
            "channel": Reminder.CHANNEL_EMAIL,
            "send_at": send_at,
            "status": Reminder.STATUS_PENDING,
        },
    )
    if not created and reminder.status == Reminder.STATUS_PENDING:
        reminder.send_at = send_at
        reminder.recipient = session.tutor.user
        reminder.save(update_fields=["send_at", "recipient"])
    return reminder


def send_reminder(reminder):
    """
    Stub delivery — mirrors apps.users.services.send_otp. Replace with a
    real email/SMS/push provider; dispatch_due_reminders doesn't need to
    change when that happens.
    """
    destination = (
        reminder.recipient.email
        if reminder.channel == Reminder.CHANNEL_EMAIL
        else reminder.recipient.phone
    )
    logger.info(
        "Reminder via %s to %s for session %s", reminder.channel, destination, reminder.session_id
    )
    print(
        f"[REMINDER STUB] {reminder.channel} to {destination}: "
        f"session {reminder.session_id} at {reminder.session.starts_at}"
    )
