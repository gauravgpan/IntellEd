from django.conf import settings
from rest_framework import permissions, viewsets

from apps.schools.models import TutorAssignment
from apps.users.models import User
from apps.users.permissions import IsFounderAdminOrTutor, IsFounderOrAdmin

from .models import ClassLessonPlan, Handout, Lesson
from .serializers import ClassLessonPlanSerializer, HandoutSerializer, LessonSerializer


class LessonViewSet(viewsets.ModelViewSet):
    """Authoring is Admin/Founder; tutors can read (needed to download
    handouts for their assigned classes' sessions)."""

    queryset = Lesson.objects.prefetch_related("handouts").all()
    serializer_class = LessonSerializer
    permission_classes = [IsFounderAdminOrTutor]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsFounderOrAdmin()]
        return super().get_permissions()


class HandoutViewSet(viewsets.ModelViewSet):
    queryset = Handout.objects.select_related("lesson").all()
    serializer_class = HandoutSerializer
    permission_classes = [IsFounderAdminOrTutor]
    filterset_fields = ["lesson", "kind"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsFounderOrAdmin()]
        return super().get_permissions()


class ClassLessonPlanViewSet(viewsets.ModelViewSet):
    """
    Open decision 7: Admin/Founder set a class's lesson sequence by default.
    settings.CLASS_PLAN_EDITABLE_BY_TUTOR flips write access to tutors too,
    scoped to their own assigned classes, once that's decided.
    """

    serializer_class = ClassLessonPlanSerializer
    permission_classes = [IsFounderAdminOrTutor]
    filterset_fields = ["school_class"]

    def get_queryset(self):
        qs = ClassLessonPlan.objects.select_related("lesson", "school_class").all()
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
            if settings.CLASS_PLAN_EDITABLE_BY_TUTOR:
                return [IsFounderAdminOrTutor()]
            return [IsFounderOrAdmin()]
        return super().get_permissions()
