from rest_framework import serializers

from .models import ClassLessonPlan, Handout, Lesson


class HandoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Handout
        fields = ["id", "lesson", "kind", "file_ref", "qr_payload"]


class LessonSerializer(serializers.ModelSerializer):
    handouts = HandoutSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = ["id", "header", "learning_objective", "board_position", "info_text", "version", "handouts"]


class ClassLessonPlanSerializer(serializers.ModelSerializer):
    lesson_header = serializers.CharField(source="lesson.header", read_only=True)

    class Meta:
        model = ClassLessonPlan
        fields = ["id", "school_class", "lesson", "lesson_header", "seq_no"]
