from rest_framework import viewsets

from apps.users.models import User
from apps.users.permissions import IsFounderAdminOrTutor, IsFounderOrAdmin

from .models import Attendance, PerformanceNote, Reminder, Session
from .serializers import AttendanceSerializer, PerformanceNoteSerializer, ReminderSerializer, SessionSerializer


class SessionViewSet(viewsets.ModelViewSet):
    """Tutors manage their own sessions; Admin/Founder see and manage all
    (design doc role table, section 9: "Create and update sessions" = Own
    sessions for Tutor, Yes for Admin/Founder)."""

    serializer_class = SessionSerializer
    permission_classes = [IsFounderAdminOrTutor]
    filterset_fields = ["school_class", "tutor", "status"]

    def get_queryset(self):
        qs = Session.objects.select_related("school_class", "tutor").all()
        user = self.request.user
        if user.role == User.ROLE_TUTOR:
            tutor = getattr(user, "tutor_profile", None)
            qs = qs.filter(tutor=tutor) if tutor else qs.none()
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == User.ROLE_TUTOR:
            serializer.save(tutor=user.tutor_profile)
        else:
            serializer.save()


class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [IsFounderAdminOrTutor]
    filterset_fields = ["session", "student", "present"]

    def get_queryset(self):
        qs = Attendance.objects.select_related("session", "student").all()
        user = self.request.user
        if user.role == User.ROLE_TUTOR:
            tutor = getattr(user, "tutor_profile", None)
            qs = qs.filter(session__tutor=tutor) if tutor else qs.none()
        return qs

    def perform_create(self, serializer):
        serializer.save(marked_by=self.request.user)


class PerformanceNoteViewSet(viewsets.ModelViewSet):
    serializer_class = PerformanceNoteSerializer
    permission_classes = [IsFounderAdminOrTutor]
    filterset_fields = ["session", "student"]

    def get_queryset(self):
        qs = PerformanceNote.objects.select_related("session", "student", "author").all()
        user = self.request.user
        if user.role == User.ROLE_TUTOR:
            tutor = getattr(user, "tutor_profile", None)
            qs = qs.filter(session__tutor=tutor) if tutor else qs.none()
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class ReminderViewSet(viewsets.ModelViewSet):
    """Admin/Founder manage; a tutor can read their own reminders. Open
    decision 5: recipients are tutors only, there are no parent accounts."""

    serializer_class = ReminderSerializer
    permission_classes = [IsFounderAdminOrTutor]
    filterset_fields = ["session", "status"]

    def get_queryset(self):
        qs = Reminder.objects.select_related("session", "recipient").all()
        user = self.request.user
        if user.role == User.ROLE_TUTOR:
            qs = qs.filter(recipient=user)
        return qs

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsFounderOrAdmin()]
        return super().get_permissions()
