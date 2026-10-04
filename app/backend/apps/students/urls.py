from rest_framework.routers import DefaultRouter

from .views import StudentViewSet, SubscriptionViewSet

router = DefaultRouter()
router.register("students", StudentViewSet, basename="student")
router.register("subscriptions", SubscriptionViewSet, basename="subscription")

urlpatterns = router.urls
