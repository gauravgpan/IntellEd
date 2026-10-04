from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import OneTimePasscode, Tutor, User
from .permissions import IsFounderOrAdmin
from .serializers import RequestOTPSerializer, TutorSerializer, UserSerializer, VerifyOTPSerializer


def _find_user(identifier):
    return User.objects.filter(Q(email__iexact=identifier) | Q(phone=identifier)).first()


class RequestOTPView(APIView):
    """POST {identifier}. Sequence diagram, design doc section 4."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = _find_user(serializer.validated_data["identifier"])

        # Same response whether or not the identifier matches, so this
        # endpoint can't be used to enumerate accounts.
        generic_ok = Response({"detail": "If that account exists, an OTP was sent."})
        if user is None or user.status != User.STATUS_ACTIVE:
            return generic_ok
        if user.role == User.ROLE_TUTOR:
            profile = getattr(user, "tutor_profile", None)
            if profile is None or profile.lifecycle_state != Tutor.LIFECYCLE_ACTIVE:
                return generic_ok

        channel = OneTimePasscode.CHANNEL_EMAIL if "@" in serializer.validated_data["identifier"] else OneTimePasscode.CHANNEL_PHONE
        services.issue_otp(user, channel)
        return generic_ok


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data["identifier"]
        code = serializer.validated_data["code"]

        user = _find_user(identifier)
        if user is None:
            return Response({"detail": "Invalid code."}, status=status.HTTP_400_BAD_REQUEST)

        otp = (
            OneTimePasscode.objects.filter(user=user, code=code, consumed_at__isnull=True)
            .order_by("-created_at")
            .first()
        )
        if otp is None or not otp.is_valid():
            return Response({"detail": "Invalid or expired code."}, status=status.HTTP_400_BAD_REQUEST)

        otp.consumed_at = timezone.now()
        otp.save(update_fields=["consumed_at"])

        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": UserSerializer(user).data})


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class TutorViewSet(viewsets.ModelViewSet):
    """
    Admin/Founder-only tutor onboarding and lifecycle management.
    Matches design doc section 4 (onboarding) and section 3 (lifecycle).
    """

    queryset = Tutor.objects.select_related("user").all()
    serializer_class = TutorSerializer
    permission_classes = [IsFounderOrAdmin]

    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        """Admin records credential/background-check outcome -> Verified."""
        tutor = self.get_object()
        bg_status = request.data.get("background_check_status", Tutor.BG_CHECK_CLEARED)
        tutor.background_check_status = bg_status
        if bg_status == Tutor.BG_CHECK_CLEARED:
            tutor.lifecycle_state = Tutor.LIFECYCLE_VERIFIED
        tutor.save(update_fields=["background_check_status", "lifecycle_state"])
        return Response(TutorSerializer(tutor).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """Verified -> Active. Open decision 1: Admin and Founder both allowed."""
        tutor = self.get_object()
        if tutor.lifecycle_state != Tutor.LIFECYCLE_VERIFIED:
            return Response(
                {"detail": "Tutor must be Verified before approval."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tutor.lifecycle_state = Tutor.LIFECYCLE_ACTIVE
        tutor.approved_by = request.user
        tutor.approved_at = timezone.now()
        tutor.save(update_fields=["lifecycle_state", "approved_by", "approved_at"])
        return Response(TutorSerializer(tutor).data)

    @action(detail=True, methods=["post"])
    def suspend(self, request, pk=None):
        tutor = self.get_object()
        tutor.lifecycle_state = Tutor.LIFECYCLE_SUSPENDED
        tutor.save(update_fields=["lifecycle_state"])
        return Response(TutorSerializer(tutor).data)

    @action(detail=True, methods=["post"])
    def reactivate(self, request, pk=None):
        tutor = self.get_object()
        if tutor.lifecycle_state not in (Tutor.LIFECYCLE_SUSPENDED, Tutor.LIFECYCLE_INACTIVE):
            return Response(
                {"detail": "Only a Suspended or Inactive tutor can be reactivated."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tutor.lifecycle_state = Tutor.LIFECYCLE_ACTIVE
        tutor.save(update_fields=["lifecycle_state"])
        return Response(TutorSerializer(tutor).data)
