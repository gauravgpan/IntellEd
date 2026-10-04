import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """OTP-first manager: accounts normally have no usable password."""

    def create_user(self, email, role, phone="", **extra):
        if not email:
            raise ValueError("Users must have an email address")
        user = self.model(email=self.normalize_email(email), role=role, phone=phone, **extra)
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra):
        extra.setdefault("role", User.ROLE_FOUNDER)
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        user = self.model(email=self.normalize_email(email), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """
    MVP app users only: Founder, Admin, Tutor. Schools, students and
    guardians exist as records elsewhere (apps.schools, apps.students) but
    have no login in this phase.
    """

    ROLE_FOUNDER = "founder"
    ROLE_ADMIN = "admin"
    ROLE_TUTOR = "tutor"
    ROLE_CHOICES = [
        (ROLE_FOUNDER, "Founder"),
        (ROLE_ADMIN, "Admin"),
        (ROLE_TUTOR, "Tutor"),
    ]

    STATUS_ACTIVE = "active"
    STATUS_INACTIVE = "inactive"
    STATUS_CHOICES = [(STATUS_ACTIVE, "Active"), (STATUS_INACTIVE, "Inactive")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    # OTP goes over both email and phone for tutors (confirmed); phone is
    # optional so Admin/Founder accounts can be email-only.
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["role"]

    class Meta:
        db_table = "user"

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def is_founder_or_admin(self):
        return self.role in (self.ROLE_FOUNDER, self.ROLE_ADMIN)


class Tutor(models.Model):
    """
    One-to-one extension of User for tutor-specific profile and lifecycle.
    Mirrors the TUTOR entity in the design doc's ER diagram (section 2) and
    the Tutor lifecycle state machine (section 3).
    """

    LIFECYCLE_APPLIED = "applied"
    LIFECYCLE_VERIFIED = "verified"
    LIFECYCLE_ACTIVE = "active"
    LIFECYCLE_SUSPENDED = "suspended"
    LIFECYCLE_INACTIVE = "inactive"
    LIFECYCLE_CHOICES = [
        (LIFECYCLE_APPLIED, "Applied"),
        (LIFECYCLE_VERIFIED, "Verified"),
        (LIFECYCLE_ACTIVE, "Active"),
        (LIFECYCLE_SUSPENDED, "Suspended"),
        (LIFECYCLE_INACTIVE, "Inactive"),
    ]
    # NOTE (open decision 2, design doc section 10): the doc's lifecycle has
    # no state for an applicant who fails verification. Nothing here blocks
    # adding LIFECYCLE_REJECTED later; it just isn't modeled yet.

    BG_CHECK_PENDING = "pending"
    BG_CHECK_CLEARED = "cleared"
    BG_CHECK_FAILED = "failed"
    BG_CHECK_CHOICES = [
        (BG_CHECK_PENDING, "Pending"),
        (BG_CHECK_CLEARED, "Cleared"),
        (BG_CHECK_FAILED, "Failed"),
    ]

    user = models.OneToOneField(
        User, primary_key=True, on_delete=models.CASCADE, related_name="tutor_profile"
    )
    full_name = models.CharField(max_length=255)
    dob = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    chess_rating = models.CharField(max_length=20, blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    background_check_status = models.CharField(
        max_length=10, choices=BG_CHECK_CHOICES, default=BG_CHECK_PENDING
    )
    lifecycle_state = models.CharField(
        max_length=10, choices=LIFECYCLE_CHOICES, default=LIFECYCLE_APPLIED
    )
    approved_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="tutors_approved"
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "tutor"

    def __str__(self):
        return self.full_name


class OneTimePasscode(models.Model):
    """
    Supports apps/users/services.py's OTP request/verify flow. Not part of
    the original ER diagram (that modeled domain data, not auth plumbing).
    """

    CHANNEL_EMAIL = "email"
    CHANNEL_PHONE = "phone"
    CHANNEL_CHOICES = [(CHANNEL_EMAIL, "Email"), (CHANNEL_PHONE, "Phone")]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otp_codes")
    channel = models.CharField(max_length=5, choices=CHANNEL_CHOICES)
    code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "one_time_passcode"
        indexes = [models.Index(fields=["user", "code", "consumed_at"])]

    def is_valid(self):
        return self.consumed_at is None and timezone.now() < self.expires_at
