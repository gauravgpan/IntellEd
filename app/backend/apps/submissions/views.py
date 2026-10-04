from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.schools.models import TutorAssignment
from apps.users.models import User
from apps.users.permissions import IsFounderAdminOrTutor

from . import services
from .models import Submission, SubmissionEntry
from .serializers import SubmissionEntrySerializer, SubmissionSerializer


class SubmissionViewSet(viewsets.ModelViewSet):
    """Design doc sections 6 and 8: upload, review/confirm, or waive."""

    serializer_class = SubmissionSerializer
    permission_classes = [IsFounderAdminOrTutor]
    filterset_fields = ["handout", "student", "status"]

    def get_queryset(self):
        qs = Submission.objects.select_related("handout", "student", "student__identity").prefetch_related("entries")
        user = self.request.user
        if user.role == User.ROLE_TUTOR:
            tutor = getattr(user, "tutor_profile", None)
            if tutor is None:
                return qs.none()
            assigned_class_ids = TutorAssignment.objects.filter(
                tutor=tutor, status=TutorAssignment.STATUS_ACTIVE
            ).values_list("school_class_id", flat=True)
            qs = qs.filter(student__school_class_id__in=assigned_class_ids)
        return qs

    def perform_create(self, serializer):
        submission = serializer.save(uploaded_by=self.request.user, uploaded_at=timezone.now())
        services.run_extraction(submission)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """
        Tutor confirms (or corrects) extracted entries before anything is
        committed to student history — design doc open decision 4: tutor
        confirmation is required, extraction is never auto-committed.
        Body: {"entries": [{"item_no": 1, "confirmed_value": "..."}]}
        """
        submission = self.get_object()
        if submission.status not in (Submission.STATUS_NEEDS_REVIEW, Submission.STATUS_FAILED):
            return Response(
                {"detail": "Only a submission in NeedsReview or Failed can be confirmed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for item in request.data.get("entries", []):
            SubmissionEntry.objects.update_or_create(
                submission=submission,
                item_no=item["item_no"],
                defaults={"confirmed_value": item.get("confirmed_value", "")},
            )
        submission.status = Submission.STATUS_CONFIRMED
        submission.reviewed_by = request.user
        submission.reviewed_at = timezone.now()
        submission.save(update_fields=["status", "reviewed_by", "reviewed_at"])
        return Response(SubmissionSerializer(submission).data)

    @action(detail=True, methods=["post"])
    def waive(self, request, pk=None):
        """
        Mark a student Waived on a handout (absence/exemption) so the class
        can still reach Done — design doc section 6 and open decision 10.
        Open decision 10 (who may waive) is unresolved; every assigned
        tutor can for now (settings.ANY_ASSIGNED_TUTOR_CAN_WAIVE).
        """
        submission = self.get_object()
        if submission.status == Submission.STATUS_CONFIRMED:
            return Response(
                {"detail": "Already confirmed; cannot waive a confirmed submission."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        submission.status = Submission.STATUS_WAIVED
        submission.waived_by = request.user
        submission.waived_reason = request.data.get("reason", "")
        submission.save(update_fields=["status", "waived_by", "waived_reason"])
        return Response(SubmissionSerializer(submission).data)

    @action(detail=True, methods=["post"], url_path="retry-extraction")
    def retry_extraction(self, request, pk=None):
        """Re-upload / Failed -> Uploaded -> re-run extraction (design doc
        section 8's 'Extraction fails' branch)."""
        submission = self.get_object()
        services.run_extraction(submission)
        return Response(SubmissionSerializer(submission).data)
