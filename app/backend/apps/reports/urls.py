from django.urls import path

from .views import StudentReportView

urlpatterns = [
    path("student/<uuid:student_token>/", StudentReportView.as_view(), name="student-report"),
]
