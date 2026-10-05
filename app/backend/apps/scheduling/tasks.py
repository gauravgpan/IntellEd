"""
Periodic background jobs. These run in the Django-Q2 worker process
(`python manage.py qcluster`), never inside a web request. Registered as a
schedule by the setup_schedules management command — see that command and
app/README.md for how to run it.
"""

import logging

from django.utils import timezone

from .models import Reminder
from .services import send_reminder

logger = logging.getLogger("thinkturf.scheduling")


def dispatch_due_reminders():
    """
    The actual "system trigger" behind the Communications module's
    Reminders Must-have (design doc §5, §10 open decision 5): nothing else
    checks the wall clock, so sending has to happen on a schedule rather
    than in response to a request.
    """
    due = Reminder.objects.filter(
        status=Reminder.STATUS_PENDING, send_at__lte=timezone.now()
    ).select_related("recipient", "session")

    sent, failed = 0, 0
    for reminder in due:
        try:
            send_reminder(reminder)
        except Exception:
            logger.exception("Failed to send reminder %s", reminder.id)
            reminder.status = Reminder.STATUS_FAILED
            failed += 1
        else:
            reminder.status = Reminder.STATUS_SENT
            sent += 1
        reminder.save(update_fields=["status"])

    logger.info("dispatch_due_reminders: %s sent, %s failed", sent, failed)
    return {"sent": sent, "failed": failed}
