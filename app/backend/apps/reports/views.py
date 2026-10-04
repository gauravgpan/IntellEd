from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assessments.models import CSSAssessment
from apps.schools.models import TutorAssignment
from apps.scheduling.models import Attendance, PerformanceNote
from apps.students.models import Student
from apps.submissions.models import Submission
from apps.users.models import User


class StudentReportView(APIView):
    """
    Individual report (design doc section 9: Founder/Admin = Yes, Tutor =
    Assigned students only). Cross-school/cohort analytics (Reports module's
    other half) is explicitly deferred — section 11.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, student_token):
        try:
            student = Student.objects.select_related("identity", "school_class").get(pk=student_token)
        except Student.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)

        user = request.user
        if user.role == User.ROLE_TUTOR:
            tutor = getattr(user, "tutor_profile", None)
            allowed = tutor and TutorAssignment.objects.filter(
                tutor=tutor, school_class=student.school_class, status=TutorAssignment.STATUS_ACTIVE
            ).exists()
            if not allowed:
                return Response({"detail": "Not found."}, status=404)

        attendance_qs = Attendance.objects.filter(student=student)
        notes = (
            PerformanceNote.objects.filter(student=student)
            .select_related("author")
            .order_by("-created_at")[:20]
        )
        latest_assessment = (
            CSSAssessment.objects.filter(student=student, status=CSSAssessment.STATUS_COMPLETED)
            .prefetch_related("domain_scores")
            .order_by("-cycle_no")
            .first()
        )
        submissions = Submission.objects.filter(student=student).select_related("handout")

        identity = getattr(student, "identity", None)

        return Response(
            {
                "student_token": str(student.student_token),
                "display_name": identity.full_name if identity else None,
                "school_class": str(student.school_class),
                "attendance": {
                    "sessions_recorded": attendance_qs.count(),
                    "present": attendance_qs.filter(present=True).count(),
                },
                "performance_notes": [
                    {"note": n.note, "author": n.author.email, "created_at": n.created_at}
                    for n in notes
                ],
                "latest_cognitive_snapshot": (
                    {
                        "cycle_no": latest_assessment.cycle_no,
                        "completed_at": latest_assessment.completed_at,
                        "domain_scores": [
                            {"domain": d.domain, "raw_score": d.raw_score, "band_label": d.band_label}
                            for d in latest_assessment.domain_scores.all()
                        ],
                    }
                    if latest_assessment
                    else None
                ),
                "handouts": [
                    {"handout_id": str(s.handout_id), "status": s.status}
                    for s in submissions
                ],
            }
        )
