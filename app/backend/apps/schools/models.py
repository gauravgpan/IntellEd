import uuid

from django.db import models


class School(models.Model):
    """Design doc ER diagram, section 2. School lifecycle: section 3."""

    STATE_ENQUIRY = "enquiry"
    STATE_AGREEMENT_SIGNED = "agreement_signed"
    STATE_ONBOARDED = "onboarded"
    STATE_ACTIVE = "active"
    STATE_CHOICES = [
        (STATE_ENQUIRY, "Enquiry"),
        (STATE_AGREEMENT_SIGNED, "Agreement signed"),
        (STATE_ONBOARDED, "Onboarded"),
        (STATE_ACTIVE, "Active"),
    ]
    # NOTE (open decision 6, design doc section 10): what moves a school from
    # Onboarded to Active is unresolved. first_session_scheduled() below is
    # the assumed trigger — called from scheduling.Session.save() when a
    # school's first session is created.

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    poc_name = models.CharField(max_length=255, blank=True)
    poc_email = models.EmailField(blank=True)
    grade_levels = models.CharField(max_length=255, blank=True, help_text="e.g. 'Grade 1-5'")
    lifecycle_state = models.CharField(max_length=20, choices=STATE_CHOICES, default=STATE_ENQUIRY)

    class Meta:
        db_table = "school"
        verbose_name_plural = "schools"

    def __str__(self):
        return self.name

    def mark_active_on_first_session(self):
        if self.lifecycle_state == self.STATE_ONBOARDED:
            self.lifecycle_state = self.STATE_ACTIVE
            self.save(update_fields=["lifecycle_state"])


class SchoolClass(models.Model):
    """A specific grade/section within a school for one academic year."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="classes")
    grade = models.CharField(max_length=50)
    section = models.CharField(max_length=10, blank=True)
    academic_year = models.CharField(max_length=20)

    class Meta:
        db_table = "school_class"
        verbose_name_plural = "school classes"
        unique_together = [("school", "grade", "section", "academic_year")]

    def __str__(self):
        label = f"{self.school.name} — Grade {self.grade}"
        return f"{label}{self.section}" if self.section else label


class TutorAssignment(models.Model):
    """Many-to-many Tutor <-> SchoolClass, per design doc's TUTOR_ASSIGNMENT."""

    STATUS_ACTIVE = "active"
    STATUS_ENDED = "ended"
    STATUS_CHOICES = [(STATUS_ACTIVE, "Active"), (STATUS_ENDED, "Ended")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tutor = models.ForeignKey("users.Tutor", on_delete=models.CASCADE, related_name="assignments")
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="tutor_assignments")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE)

    class Meta:
        db_table = "tutor_assignment"

    def __str__(self):
        return f"{self.tutor.full_name} -> {self.school_class}"
