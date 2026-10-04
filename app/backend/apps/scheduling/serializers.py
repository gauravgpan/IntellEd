from rest_framework import serializers

from .models import Attendance, PerformanceNote, Reminder, Session


class SessionSerializer(serializers.ModelSerializer):
    class_label = serializers.CharField(source="school_class.__str__", read_only=True)
    tutor_name = serializers.CharField(source="tutor.full_name", read_only=True)

    class Meta:
        model = Session
        fields = [
            "id", "school_class", "class_label", "tutor", "tutor_name",
            "lesson", "starts_at", "ends_at", "status",
        ]


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ["id", "session", "student", "present", "marked_by"]
        read_only_fields = ["marked_by"]


class PerformanceNoteSerializer(serializers.ModelSerializer):
    author_email = serializers.CharField(source="author.email", read_only=True)

    class Meta:
        model = PerformanceNote
        fields = ["id", "session", "student", "note", "author", "author_email", "created_at"]
        read_only_fields = ["author", "created_at"]


class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = ["id", "session", "recipient", "channel", "send_at", "status"]
