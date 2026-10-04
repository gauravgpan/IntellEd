"""
The class view (design doc section 6) is a derived read model: nothing here
is stored beyond the one new table, ClassLessonPlan. Handout status is
computed from the plan, the live roster and Submission rows.
"""

from django.conf import settings

from apps.curriculum.models import ClassLessonPlan, Handout
from apps.students.models import Student
from apps.submissions.models import Submission

STATUS_TO_DO = "to_do"
STATUS_IN_PROGRESS = "in_progress"
STATUS_DONE = "done"


def class_view(school_class):
    students = list(
        Student.objects.filter(school_class=school_class, status=Student.STATUS_ACTIVE).select_related("identity")
    )
    strength = len(students)
    student_ids = [s.student_token for s in students]

    plan_entries = (
        ClassLessonPlan.objects.filter(school_class=school_class)
        .select_related("lesson")
        .order_by("seq_no")
    )

    done_statuses = settings.SUBMISSION_STATUSES_COUNTED_AS_DONE

    handouts_progress = []
    for entry in plan_entries:
        for handout in Handout.objects.filter(lesson=entry.lesson):
            qs = Submission.objects.filter(handout=handout, student_id__in=student_ids)
            confirmed = qs.filter(status=Submission.STATUS_CONFIRMED).count()
            waived = qs.filter(status=Submission.STATUS_WAIVED).count()
            done_count = qs.filter(status__in=done_statuses).count()

            if strength == 0:
                hstatus = STATUS_TO_DO
            elif done_count >= strength:
                hstatus = STATUS_DONE
            elif done_count > 0:
                hstatus = STATUS_IN_PROGRESS
            else:
                hstatus = STATUS_TO_DO

            handouts_progress.append(
                {
                    "handout_id": str(handout.id),
                    "lesson_id": str(entry.lesson_id),
                    "lesson_header": entry.lesson.header,
                    "seq_no": entry.seq_no,
                    "kind": handout.kind,
                    "status": hstatus,
                    "confirmed": confirmed,
                    "waived": waived,
                    "total": strength,
                }
            )

    handouts_planned = plan_entries.count()
    roster = []
    for student in students:
        submitted = Submission.objects.filter(student=student, status__in=done_statuses).count()
        identity = getattr(student, "identity", None)
        roster.append(
            {
                "student_token": str(student.student_token),
                "display_name": identity.full_name if identity else None,
                "handouts_submitted": submitted,
                "handouts_planned": handouts_planned,
            }
        )

    return {
        "school_class_id": str(school_class.id),
        "label": str(school_class),
        "strength": strength,
        "roster": roster,
        "handouts": handouts_progress,
    }
