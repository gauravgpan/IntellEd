from rest_framework.routers import DefaultRouter

from .views import CSSAssessmentViewSet, ConsentRecordViewSet

router = DefaultRouter()
router.register("consent-records", ConsentRecordViewSet, basename="consent-record")
router.register("css-assessments", CSSAssessmentViewSet, basename="css-assessment")

urlpatterns = router.urls
