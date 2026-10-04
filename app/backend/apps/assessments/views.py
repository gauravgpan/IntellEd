from django.db.models import Max
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.schools.models import TutorAssignment
from apps.users.models import User
from apps.users.permissions import IsFounderAdminOrTutor

from .models import CSSAssessment, CSSDomainScore, ConsentRecord
from .serializers import CSSAssessmentSerializer, ConsentRecordSerializer


def _tutor_student_scope(request, qs, student_field="student__school_class_id"):
    user = request.user
    if user.role == User.ROLE_TUTOR:
        tutor = getattr(user, "tutor_profile", None)
        if tutor is None:
            return qs.none()
        assigned_class_ids = TutorAssignment.objects.filter(
            tutor=tutor, status=TutorAssignment.STATUS_ACTIVE
        ).values_list("school_class_id", flat=True)
        qs = qs.filter(**{f"{student_field}__in": assigned_class_ids})
    return qs


class ConsentRecordViewSet(viewsets.ModelViewSet):
    """
    Open decision 3: how consent is evidenced isn't settled — this just
    records the outcome (granted/revoked), captured by whoever enters it.
    """

    serializer_class = ConsentRecordSerializer
    permission_classes = [IsFounderAdminOrTutor]
    filterset_fields = ["student", "status", "scope"]

    def get_queryset(self):
        return _tutor_student_scope(self.request, ConsentRecord.objects.select_related("student").all())

    def perform_create(self, serializer):
        serializer.save(captured_by=self.request.user)


class CSSAssessmentViewSet(viewsets.ModelViewSet):
    """Design doc section 7's sequence diagram: blocked without consent,
    cycle_no auto-increments per student, scores saved via /complete/."""

    serializer_class = CSSAssessmentSerializer
    permission_classes = [IsFounderAdminOrTutor]
    filterset_fields = ["student", "status"]

    def get_queryset(self):
        return _tutor_student_scope(
            self.request, CSSAssessment.objects.select_related("student").prefetch_related("domain_scores")
        )

    def create(self, request, *args, **kwargs):
        student_id = request.data.get("student")
        consent = (
            ConsentRecord.objects.filter(
                student_id=student_id, scope="cognitive_assessment", status=ConsentRecord.STATUS_GRANTED
            )
            .order_by("-captured_at")
            .first()
        )
        if consent is None:
            return Response(
                {"detail": "Blocked: no valid consent on file for this student."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        last_cycle = (
            CSSAssessment.objects.filter(student_id=student_id).aggregate(m=Max("cycle_no"))["m"] or 0
        )
        assessment = CSSAssessment.objects.create(
            student_id=student_id,
            consent=consent,
            age_band=request.data.get("age_band"),
            cycle_no=last_cycle + 1,
        )
        return Response(CSSAssessmentSerializer(assessment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Body: {"domain_scores": [{"domain": "...", "raw_score": 0, "band_label": "..."}, ...]}"""
        assessment = self.get_object()
        for entry in request.data.get("domain_scores", []):
            CSSDomainScore.objects.update_or_create(
                assessment=assessment,
                domain=entry["domain"],
                defaults={"raw_score": entry["raw_score"], "band_label": entry.get("band_label", "")},
            )
        assessment.status = CSSAssessment.STATUS_COMPLETED
        assessment.completed_at = timezone.now()
        assessment.save(update_fields=["status", "completed_at"])
        return Response(CSSAssessmentSerializer(assessment).data)
