from django.contrib import admin

from .models import CSSAssessment, CSSDomainScore, ConsentRecord


class CSSDomainScoreInline(admin.TabularInline):
    model = CSSDomainScore
    extra = 0


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ["student", "scope", "status", "captured_by", "captured_at"]
    list_filter = ["status", "scope"]


@admin.register(CSSAssessment)
class CSSAssessmentAdmin(admin.ModelAdmin):
    list_display = ["student", "cycle_no", "age_band", "status", "started_at", "completed_at"]
    list_filter = ["status", "age_band"]
    inlines = [CSSDomainScoreInline]
