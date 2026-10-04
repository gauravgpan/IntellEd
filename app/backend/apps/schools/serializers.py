from rest_framework import serializers

from .models import School, SchoolClass, TutorAssignment


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ["id", "name", "address", "poc_name", "poc_email", "grade_levels", "lifecycle_state"]
        read_only_fields = ["lifecycle_state"]


class SchoolClassSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source="school.name", read_only=True)

    class Meta:
        model = SchoolClass
        fields = ["id", "school", "school_name", "grade", "section", "academic_year"]


class TutorAssignmentSerializer(serializers.ModelSerializer):
    tutor_name = serializers.CharField(source="tutor.full_name", read_only=True)
    class_label = serializers.CharField(source="school_class.__str__", read_only=True)

    class Meta:
        model = TutorAssignment
        fields = ["id", "tutor", "tutor_name", "school_class", "class_label", "start_date", "end_date", "status"]
