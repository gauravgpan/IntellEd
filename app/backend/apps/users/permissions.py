from rest_framework.permissions import BasePermission

from .models import User


class IsFounderOrAdmin(BasePermission):
    """Founder and Admin are treated as equally privileged throughout the MVP
    (design doc section 9's role table gives them identical 'Yes' columns)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_founder_or_admin)


class IsTutor(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.ROLE_TUTOR)


class IsFounderAdminOrTutor(BasePermission):
    """Any authenticated MVP app user. Per-object / per-queryset scoping
    (e.g. a tutor only seeing their assigned classes) happens in each
    view's get_queryset, not here."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
