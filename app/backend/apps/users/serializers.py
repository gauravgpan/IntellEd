from rest_framework import serializers

from .models import OneTimePasscode, Tutor, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "phone", "role", "status", "date_joined"]
        read_only_fields = fields


class TutorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    email = serializers.EmailField(write_only=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Tutor
        fields = [
            "user",
            "email",
            "phone",
            "full_name",
            "dob",
            "address",
            "chess_rating",
            "experience_years",
            "background_check_status",
            "lifecycle_state",
            "approved_by",
            "approved_at",
        ]
        read_only_fields = ["background_check_status", "lifecycle_state", "approved_by", "approved_at"]

    def create(self, validated_data):
        email = validated_data.pop("email")
        phone = validated_data.pop("phone", "")
        user = User.objects.create_user(email=email, role=User.ROLE_TUTOR, phone=phone)
        return Tutor.objects.create(user=user, **validated_data)


class RequestOTPSerializer(serializers.Serializer):
    identifier = serializers.CharField(help_text="Email or phone the account was created with")


class VerifyOTPSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    code = serializers.CharField(max_length=10)
