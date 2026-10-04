import uuid

from django.db import models

from apps.schools.models import SchoolClass


class Student(models.Model):
    """
    Pseudonymous core record. All PII lives in StudentIdentity — this split
    is load-bearing (see principles-and-ways-of-working.md): academic-outcome
    correlation uses the token, never the name.
    """

    AGE_BAND_A = "A"
    AGE_BAND_B = "B"
    AGE_BAND_C = "C"
    AGE_BAND_CHOICES = [(AGE_BAND_A, "A"), (AGE_BAND_B, "B"), (AGE_BAND_C, "C")]

    STATUS_ACTIVE = "active"
    STATUS_INACTIVE = "inactive"
    STATUS_CHOICES = [(STATUS_ACTIVE, "Active"), (STATUS_INACTIVE, "Inactive")]

    student_token = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.PROTECT, related_name="students")
    age_band = models.CharField(max_length=1, choices=AGE_BAND_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    enrolled_at = models.DateField(auto_now_add=True)
    # NOTE (open decision 9, design doc section 10): a mid-year joiner's
    # enrolled_at lets a future "Done" calculation exclude handouts planned
    # before they joined — not yet wired into schools.services.class_view().

    class Meta:
        db_table = "student"

    def __str__(self):
        return str(self.student_token)


class StudentIdentity(models.Model):
    """All PII, keyed 1:1 to the pseudonymous Student. Also carries the
    school's own student ID (the school-ID-to-unique-ID mapping)."""

    student = models.OneToOneField(
        Student, primary_key=True, on_delete=models.CASCADE, related_name="identity"
    )
    school_student_id = models.CharField(max_length=100, blank=True)
    full_name = models.CharField(max_length=255)
    dob = models.DateField(null=True, blank=True)
    guardian_name = models.CharField(max_length=255, blank=True)
    guardian_email = models.EmailField(blank=True)

    class Meta:
        db_table = "student_identity"
        verbose_name_plural = "student identities"

    def __str__(self):
        return self.full_name


class Subscription(models.Model):
    STATE_TRIAL_PENDING = "trial_pending"
    STATE_ACTIVE = "active"
    STATE_LAPSED = "lapsed"
    STATE_CHOICES = [
        (STATE_TRIAL_PENDING, "Trial pending"),
        (STATE_ACTIVE, "Active"),
        (STATE_LAPSED, "Lapsed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="subscriptions")
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default=STATE_TRIAL_PENDING)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "subscription"

    def __str__(self):
        return f"{self.student_id} — {self.state}"
