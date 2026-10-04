from django.contrib import admin

from .models import School, SchoolClass, TutorAssignment


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ["name", "lifecycle_state", "poc_name", "poc_email"]
    list_filter = ["lifecycle_state"]
    search_fields = ["name"]


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ["school", "grade", "section", "academic_year"]
    list_filter = ["school", "academic_year"]


@admin.register(TutorAssignment)
class TutorAssignmentAdmin(admin.ModelAdmin):
    list_display = ["tutor", "school_class", "status", "start_date", "end_date"]
    list_filter = ["status"]
