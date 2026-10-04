from rest_framework.routers import DefaultRouter

from .views import AttendanceViewSet, PerformanceNoteViewSet, ReminderViewSet, SessionViewSet

router = DefaultRouter()
router.register("sessions", SessionViewSet, basename="session")
router.register("attendance", AttendanceViewSet, basename="attendance")
router.register("performance-notes", PerformanceNoteViewSet, basename="performance-note")
router.register("reminders", ReminderViewSet, basename="reminder")

urlpatterns = router.urls
