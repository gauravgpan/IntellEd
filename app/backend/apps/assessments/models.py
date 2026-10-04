import uuid

from django.conf import settings
from django.db import models

from apps.students.models import Student


class ConsentRecord(models.Model):
    STATUS_GRANTED = "granted"
    STATUS_REVOKED = "revoked"
    STATUS_CHOICES = [(STATUS_GRANTED, "Granted"), (STATUS_REVOKED, "Revoked")]

    # NOTE (open decision 3, design doc section 10): with no parent login,
    # how consent is actually evidenced (paper form uploaded? collected by
    # the school?) is unresolved. This model only records the outcome.

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="consent_records")
    scope = models.CharField(max_length=100, default="cognitive_assessment")
    consent_version = models.CharField(max_length=20)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_GRANTED)
    captured_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="consents_captured")
    captured_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "consent_record"

    def __str__(self):
        return f"{self.student_id} — {self.scope} ({self.status})"


class CSSAssessment(models.Model):
    """Cognitive Skill Snapshot. Design doc section 7's sequence diagram."""

    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = [(STATUS_IN_PROGRESS, "In progress"), (STATUS_COMPLETED, "Completed")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="css_assessments")
    consent = models.ForeignKey(ConsentRecord, on_delete=models.PROTECT, related_name="assessments")
    age_band = models.CharField(max_length=1, choices=Student.AGE_BAND_CHOICES)
    cycle_no = models.PositiveIntegerField(default=1, help_text="A six-month re-assessment is cycle_no + 1")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_IN_PROGRESS)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "css_assessment"
        unique_together = [("student", "cycle_no")]
        ordering = ["-cycle_no"]

    def __str__(self):
        return f"{self.student_id} cycle {self.cycle_no}"


class CSSDomainScore(models.Model):
    """
    One row per domain per assessment (six rows per completed CSSAssessment).
    The six domain names/CHC mapping aren't specified in the design
    materials yet — `domain` is free text until that's confirmed, rather
    than guessed-at hardcoded choices.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(CSSAssessment, on_delete=models.CASCADE, related_name="domain_scores")
    domain = models.CharField(max_length=100)
    raw_score = models.FloatField()
    band_label = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "css_domain_score"
        unique_together = [("assessment", "domain")]

    def __str__(self):
        return f"{self.assessment_id} / {self.domain}"
