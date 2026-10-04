from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from apps.users.models import User
from apps.users.permissions import IsFounderAdminOrTutor, IsFounderOrAdmin

from . import services
from .models import School, SchoolClass, TutorAssignment
from .serializers import SchoolClassSerializer, SchoolSerializer, TutorAssignmentSerializer


class SchoolViewSet(viewsets.ModelViewSet):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [IsFounderOrAdmin]


class TutorAssignmentViewSet(viewsets.ModelViewSet):
    queryset = TutorAssignment.objects.select_related("tutor", "school_class").all()
    serializer_class = TutorAssignmentSerializer
    permission_classes = [IsFounderOrAdmin]


class SchoolClassViewSet(viewsets.ModelViewSet):
    """
    List/search is scoped to the requesting tutor's assigned classes
    (design doc section 6: "limited to classes they are assigned to").
    Admin/Founder see everything.
    """

    serializer_class = SchoolClassSerializer
    permission_classes = [IsFounderAdminOrTutor]
    filterset_fields = ["school", "grade", "section", "academic_year"]
    # Free-text search, e.g. GET /api/classes/?search=grade+4 — design doc
    # section 6: "or by searching".
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["grade", "section", "academic_year", "school__name"]

    def get_queryset(self):
        qs = SchoolClass.objects.select_related("school").all()
        user = self.request.user
        if user.role == User.ROLE_TUTOR:
            tutor = getattr(user, "tutor_profile", None)
            if tutor is None:
                return qs.none()
            qs = qs.filter(tutor_assignments__tutor=tutor, tutor_assignments__status=TutorAssignment.STATUS_ACTIVE)
        return qs.distinct()

    @action(detail=True, methods=["get"], url_path="class-view")
    def class_view(self, request, pk=None):
        """GET /api/classes/{id}/class-view/ — design doc section 6."""
        school_class = self.get_object()  # get_queryset already enforces assignment scoping
        return Response(services.class_view(school_class))
