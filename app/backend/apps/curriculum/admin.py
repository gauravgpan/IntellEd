from django.contrib import admin

from .models import ClassLessonPlan, Handout, Lesson


class HandoutInline(admin.TabularInline):
    model = Handout
    extra = 0


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["header", "version"]
    search_fields = ["header"]
    inlines = [HandoutInline]


@admin.register(Handout)
class HandoutAdmin(admin.ModelAdmin):
    list_display = ["lesson", "kind", "qr_payload"]
    list_filter = ["kind"]


@admin.register(ClassLessonPlan)
class ClassLessonPlanAdmin(admin.ModelAdmin):
    list_display = ["school_class", "seq_no", "lesson"]
    list_filter = ["school_class"]
    ordering = ["school_class", "seq_no"]
