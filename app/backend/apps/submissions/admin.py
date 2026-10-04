from django.contrib import admin

from .models import Submission, SubmissionEntry


class SubmissionEntryInline(admin.TabularInline):
    model = SubmissionEntry
    extra = 0


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ["student", "handout", "status", "uploaded_at", "reviewed_by", "waived_by"]
    list_filter = ["status"]
    inlines = [SubmissionEntryInline]
