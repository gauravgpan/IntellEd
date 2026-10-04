import uuid

from django.conf import settings
from django.db import models

from apps.curriculum.models import Lesson
from apps.schools.models import SchoolClass


class Session(models.Model):
    STATUS_SCHEDULED = "scheduled"
    STATUS_HELD = "held"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_SCHEDULED, "Scheduled"),
        (STATUS_HELD, "Held"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="sessions")
    tutor = models.ForeignKey("users.Tutor", on_delete=models.PROTECT, related_name="sessions")
    lesson = models.ForeignKey(Lesson, null=True, blank=True, on_delete=models.SET_NULL, related_name="sessions")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_SCHEDULED)

    class Meta:
        db_table = "session"
        ordering = ["starts_at"]

    def __str__(self):
        return f"{self.school_class} @ {self.starts_at:%Y-%m-%d %H:%M}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            # Open decision 6: a school's first session is the assumed
            # Onboarded -> Active trigger (design doc section 3).
            self.school_class.school.mark_active_on_first_session()


class Attendance(models.Model):
    """
    Logically keyed by (session, student) — the design doc's ER diagram
    gives this a composite primary key. Django models this with a surrogate
    id plus a unique_together constraint instead of a true composite PK.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="attendance_records")
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="attendance_records")
    present = models.BooleanField(default=True)
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="attendance_marked")

    class Meta:
        db_table = "attendance"
        unique_together = [("session", "student")]

    def __str__(self):
        return f"{self.student_id} @ {self.session_id}: {'present' if self.present else 'absent'}"


class PerformanceNote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="performance_notes")
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="performance_notes")
    note = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="performance_notes_authored")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "performance_note"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note on {self.student_id} ({self.created_at:%Y-%m-%d})"


class Reminder(models.Model):
    CHANNEL_EMAIL = "email"
    CHANNEL_SMS = "sms"
    CHANNEL_PUSH = "push"
    CHANNEL_CHOICES = [(CHANNEL_EMAIL, "Email"), (CHANNEL_SMS, "SMS"), (CHANNEL_PUSH, "Push")]

    STATUS_PENDING = "pending"
    STATUS_SENT = "sent"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [(STATUS_PENDING, "Pending"), (STATUS_SENT, "Sent"), (STATUS_FAILED, "Failed")]

    # NOTE (open decision 5, design doc section 10): recipients are tutors
    # only for now — there are no parent accounts in this MVP.

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="reminders")
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reminders")
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default=CHANNEL_EMAIL)
    send_at = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)

    class Meta:
        db_table = "reminder"
        ordering = ["send_at"]

    def __str__(self):
        return f"Reminder for {self.recipient} @ {self.send_at}"
