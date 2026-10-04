from rest_framework import serializers

from .models import Student, StudentIdentity, Subscription


class StudentIdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentIdentity
        fields = ["school_student_id", "full_name", "dob", "guardian_name", "guardian_email"]


class StudentSerializer(serializers.ModelSerializer):
    identity = StudentIdentitySerializer()

    class Meta:
        model = Student
        fields = ["student_token", "school_class", "age_band", "status", "enrolled_at", "identity"]
        read_only_fields = ["student_token", "enrolled_at"]

    def create(self, validated_data):
        identity_data = validated_data.pop("identity")
        student = Student.objects.create(**validated_data)
        StudentIdentity.objects.create(student=student, **identity_data)
        return student

    def update(self, instance, validated_data):
        identity_data = validated_data.pop("identity", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if identity_data:
            identity = instance.identity
            for attr, value in identity_data.items():
                setattr(identity, attr, value)
            identity.save()
        return instance


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ["id", "student", "state", "start_date", "end_date"]
