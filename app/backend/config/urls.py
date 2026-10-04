from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.users.urls")),
    # Each app below registers its own DRF router with distinct resource
    # names (schools/classes, students/subscriptions, lessons/handouts, …),
    # so they share one flat "api/" prefix rather than nesting per app.
    path("api/", include("apps.schools.urls")),
    path("api/", include("apps.students.urls")),
    path("api/", include("apps.curriculum.urls")),
    path("api/", include("apps.scheduling.urls")),
    path("api/", include("apps.submissions.urls")),
    path("api/", include("apps.assessments.urls")),
    path("api/reports/", include("apps.reports.urls")),
]
