"""
Registers the periodic jobs this app needs as Django-Q2 schedules. Safe to
re-run (idempotent via get_or_create) — run it once after migrating, and
again any time a schedule's interval changes.

    python manage.py setup_schedules
"""

from django.core.management.base import BaseCommand
from django_q.models import Schedule


class Command(BaseCommand):
    help = "Register this app's Django-Q2 periodic schedules (idempotent)."

    def handle(self, *args, **options):
        schedule, created = Schedule.objects.get_or_create(
            name="dispatch-due-reminders",
            defaults={
                "func": "apps.scheduling.tasks.dispatch_due_reminders",
                "schedule_type": Schedule.MINUTES,
                "minutes": 15,
                "repeats": -1,
            },
        )
        verb = "Created" if created else "Already registered"
        self.stdout.write(
            self.style.SUCCESS(f"{verb}: {schedule.name} (every {schedule.minutes} min)")
        )
