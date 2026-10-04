from rest_framework.routers import DefaultRouter

from .views import ClassLessonPlanViewSet, HandoutViewSet, LessonViewSet

router = DefaultRouter()
router.register("lessons", LessonViewSet, basename="lesson")
router.register("handouts", HandoutViewSet, basename="handout")
router.register("class-lesson-plan", ClassLessonPlanViewSet, basename="class-lesson-plan")

urlpatterns = router.urls
