import uuid

from django.conf import settings
from django.db import models

from apps.curriculum.models import Handout
from apps.students.models import Student


class Submission(models.Model):
    """
    Design doc section 7/8's upload -> extract -> review -> confirm flow,
    plus the Waived path added for students who are absent or exempt from a
    handout (so a class can still reach 'Done' — design doc section 6).
    """

    STATUS_UPLOADED = "uploaded"
    STATUS_PROCESSING = "processing"
    STATUS_NEEDS_REVIEW = "needs_review"
    STATUS_FAILED = "failed"
    STATUS_CONFIRMED = "confirmed"
    STATUS_WAIVED = "waived"
    STATUS_CHOICES = [
        (STATUS_UPLOADED, "Uploaded"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_NEEDS_REVIEW, "Needs review"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_WAIVED, "Waived"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    handout = models.ForeignKey(Handout, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="submissions")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="submissions_uploaded"
    )
    image_ref = models.CharField(max_length=500, blank=True, help_text="Object storage key/URL")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_UPLOADED)
    uploaded_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="submissions_reviewed"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    # Open decision 10: any tutor assigned to the class may waive, not just a
    # lead tutor (settings.ANY_ASSIGNED_TUTOR_CAN_WAIVE).
    waived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="submissions_waived"
    )
    waived_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "submission"
        unique_together = [("handout", "student")]

    def __str__(self):
        return f"{self.student_id} / {self.handout_id}: {self.status}"


class SubmissionEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="entries")
    item_no = models.PositiveIntegerField()
    extracted_value = models.CharField(max_length=255, blank=True)
    confirmed_value = models.CharField(max_length=255, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "submission_entry"
        unique_together = [("submission", "item_no")]
        ordering = ["item_no"]

    def __str__(self):
        return f"{self.submission_id} #{self.item_no}"
