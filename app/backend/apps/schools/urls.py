from rest_framework.routers import DefaultRouter

from .views import SchoolClassViewSet, SchoolViewSet, TutorAssignmentViewSet

router = DefaultRouter()
router.register("schools", SchoolViewSet, basename="school")
router.register("classes", SchoolClassViewSet, basename="school-class")
router.register("tutor-assignments", TutorAssignmentViewSet, basename="tutor-assignment")

urlpatterns = router.urls
