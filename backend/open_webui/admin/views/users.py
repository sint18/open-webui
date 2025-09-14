from __future__ import annotations

from starlette_admin import fields
from starlette_admin.contrib.sqla import ModelView

from open_webui.admin.fields import EpochDateTimeField, Base64ImageField
from open_webui.models.users import User

User.__admin_repr__ = lambda self, request: self.email


class UserAdmin(ModelView):
    label = "Users"
    icon = "fa fa-user"

    exclude_fields_from_list = [
        "profile_image_url", "api_key", "oauth_sub", "telegram_onboarding_token", "telegram_onboarding_token_expires_at", "settings", "info"
    ]
    exclude_fields_from_create = ["profile_image_url"]
    exclude_fields_from_edit = ["profile_image_url"]

    fields = [
        "id",
        fields.StringField("name", required=True),
        fields.StringField("email", required=True),
        fields.StringField("role", required=True),
        fields.TextAreaField("profile_image_url", read_only=True),
        fields.StringField("telegram_chat_id", required=False),
        fields.StringField("telegram_onboarding_token", required=False),
        EpochDateTimeField("telegram_onboarding_token_expires_at", label="TG Token Expires", read_only=True),
        EpochDateTimeField("last_active_at", label="Last Active", read_only=True),
        EpochDateTimeField("updated_at", label="Updated", read_only=True),
        EpochDateTimeField("created_at", label="Created", read_only=True),
        fields.StringField("api_key", required=False),
        fields.JSONField("settings"),
        fields.JSONField("info"),
        fields.TextAreaField("oauth_sub", required=False),
    ]

    list_columns = [
        "id", "name", "email", "role", "last_active_at", "created_at"
    ]

    sortable_fields = [
        "name", "email", "role", "last_active_at", "created_at", "updated_at"
    ]

    search_fields = ["name", "email", "role", "id"]


VIEWS = [UserAdmin(User)]
