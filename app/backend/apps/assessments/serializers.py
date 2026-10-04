from rest_framework import serializers

from .models import CSSAssessment, CSSDomainScore, ConsentRecord


class ConsentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsentRecord
        fields = ["id", "student", "scope", "consent_version", "status", "captured_by", "captured_at"]
        read_only_fields = ["captured_by", "captured_at"]


class CSSDomainScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSSDomainScore
        fields = ["id", "domain", "raw_score", "band_label"]


class CSSAssessmentSerializer(serializers.ModelSerializer):
    domain_scores = CSSDomainScoreSerializer(many=True, read_only=True)

    class Meta:
        model = CSSAssessment
        fields = [
            "id", "student", "consent", "age_band", "cycle_no",
            "status", "started_at", "completed_at", "domain_scores",
        ]
        read_only_fields = ["cycle_no", "started_at", "completed_at"]
