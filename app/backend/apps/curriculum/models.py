import uuid

from django.db import models

from apps.schools.models import SchoolClass


class Lesson(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    header = models.CharField(max_length=255)
    learning_objective = models.TextField(blank=True)
    board_position = models.CharField(max_length=255, blank=True, help_text="FEN or similar reference")
    info_text = models.TextField(blank=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "lesson"

    def __str__(self):
        return self.header


class Handout(models.Model):
    KIND_HANDOUT = "handout"
    KIND_ASSIGNMENT = "assignment"
    KIND_CHOICES = [(KIND_HANDOUT, "Handout"), (KIND_ASSIGNMENT, "Assignment")]
    # Physical/uploaded assessments and "assignments" are the same thing
    # (confirmed): downloaded, completed on paper, uploaded as an image.

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="handouts")
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default=KIND_ASSIGNMENT)
    file_ref = models.CharField(max_length=500, blank=True, help_text="Object storage key/URL")
    qr_payload = models.CharField(max_length=255, blank=True, help_text="Printed on the handout to identify it on upload")

    class Meta:
        db_table = "handout"

    def __str__(self):
        return f"{self.lesson.header} — {self.get_kind_display()}"


class ClassLessonPlan(models.Model):
    """
    The ordered lessons planned for a class — the one new table the class
    view (design doc section 6) needed. Admin/Founder-owned in this MVP
    (open decision 7): settings.CLASS_PLAN_EDITABLE_BY_TUTOR gates whether
    tutors may also edit it.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="lesson_plan")
    lesson = models.ForeignKey(Lesson, on_delete=models.PROTECT, related_name="class_plans")
    seq_no = models.PositiveIntegerField()

    class Meta:
        db_table = "class_lesson_plan"
        unique_together = [("school_class", "seq_no")]
        ordering = ["seq_no"]

    def __str__(self):
        return f"{self.school_class} #{self.seq_no}: {self.lesson.header}"
