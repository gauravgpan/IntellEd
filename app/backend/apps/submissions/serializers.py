from rest_framework import serializers

from .models import Submission, SubmissionEntry


class SubmissionEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionEntry
        fields = ["id", "submission", "item_no", "extracted_value", "confirmed_value", "confidence", "score"]


class SubmissionSerializer(serializers.ModelSerializer):
    entries = SubmissionEntrySerializer(many=True, read_only=True)
    student_name = serializers.CharField(source="student.identity.full_name", read_only=True, default=None)

    class Meta:
        model = Submission
        fields = [
            "id", "handout", "student", "student_name", "uploaded_by", "image_ref",
            "status", "uploaded_at", "reviewed_by", "reviewed_at",
            "waived_by", "waived_reason", "entries",
        ]
        read_only_fields = ["status", "uploaded_at", "reviewed_by", "reviewed_at", "waived_by"]
