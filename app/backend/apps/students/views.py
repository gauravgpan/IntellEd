from rest_framework import viewsets

from apps.schools.models import TutorAssignment
from apps.users.models import User
from apps.users.permissions import IsFounderAdminOrTutor, IsFounderOrAdmin

from .models import Student, Subscription
from .serializers import StudentSerializer, SubscriptionSerializer


class StudentViewSet(viewsets.ModelViewSet):
    """Create/update is Admin/Founder (onboarding); tutors can read students
    in their assigned classes (needed by the class view and student detail)."""

    serializer_class = StudentSerializer
    permission_classes = [IsFounderAdminOrTutor]
    filterset_fields = ["school_class", "status"]

    def get_queryset(self):
        qs = Student.objects.select_related("identity", "school_class").all()
        user = self.request.user
        if user.role == User.ROLE_TUTOR:
            tutor = getattr(user, "tutor_profile", None)
            if tutor is None:
                return qs.none()
            assigned_class_ids = TutorAssignment.objects.filter(
                tutor=tutor, status=TutorAssignment.STATUS_ACTIVE
            ).values_list("school_class_id", flat=True)
            qs = qs.filter(school_class_id__in=assigned_class_ids)
        return qs

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsFounderOrAdmin()]
        return super().get_permissions()


class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.select_related("student").all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsFounderOrAdmin]
    filterset_fields = ["student", "state"]
