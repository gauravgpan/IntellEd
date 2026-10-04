from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import OneTimePasscode, Tutor, User


class ThinkTurfUserCreationForm(UserCreationForm):
    # Django's default UserCreationForm.Meta hardcodes fields=("username",);
    # our User has no username field, so this must be overridden rather than
    # left to the DjangoUserAdmin default (it would error on model admin
    # load otherwise).
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "role", "phone")


class ThinkTurfUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    form = ThinkTurfUserChangeForm
    add_form = ThinkTurfUserCreationForm
    list_display = ["email", "phone", "role", "status", "is_staff"]
    list_filter = ["role", "status"]
    search_fields = ["email", "phone"]
    ordering = ["email"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("phone", "role", "status")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "role", "phone", "password1", "password2")}),
    )


@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    list_display = ["full_name", "user", "lifecycle_state", "background_check_status"]
    list_filter = ["lifecycle_state", "background_check_status"]
    search_fields = ["full_name", "user__email"]


@admin.register(OneTimePasscode)
class OneTimePasscodeAdmin(admin.ModelAdmin):
    list_display = ["user", "channel", "created_at", "expires_at", "consumed_at"]
    list_filter = ["channel"]
    readonly_fields = ["code"]
