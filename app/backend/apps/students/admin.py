from django.contrib import admin

from .models import Student, StudentIdentity, Subscription


class StudentIdentityInline(admin.StackedInline):
    model = StudentIdentity
    can_delete = False


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["student_token", "school_class", "age_band", "status"]
    list_filter = ["school_class", "age_band", "status"]
    inlines = [StudentIdentityInline]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["student", "state", "start_date", "end_date"]
    list_filter = ["state"]
