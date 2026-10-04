from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MeView, RequestOTPView, TutorViewSet, VerifyOTPView

router = DefaultRouter()
router.register("tutors", TutorViewSet, basename="tutor")

urlpatterns = [
    path("otp/request/", RequestOTPView.as_view(), name="otp-request"),
    path("otp/verify/", VerifyOTPView.as_view(), name="otp-verify"),
    path("me/", MeView.as_view(), name="me"),
    path("", include(router.urls)),
]
