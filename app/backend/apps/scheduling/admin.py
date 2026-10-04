from django.contrib import admin

from .models import Attendance, PerformanceNote, Reminder, Session


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ["school_class", "tutor", "starts_at", "status"]
    list_filter = ["status"]
    date_hierarchy = "starts_at"


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ["session", "student", "present", "marked_by"]
    list_filter = ["present"]


@admin.register(PerformanceNote)
class PerformanceNoteAdmin(admin.ModelAdmin):
    list_display = ["session", "student", "author", "created_at"]


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ["session", "recipient", "channel", "send_at", "status"]
    list_filter = ["channel", "status"]
