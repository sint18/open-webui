from __future__ import annotations

from starlette_admin import fields
from starlette_admin.contrib.sqla import ModelView

from open_webui.admin.fields import EpochDateTimeField
from open_webui.models.quota_policy import QuotaPolicy


WINDOW_CHOICES = [
    ("3h", "3 hours"),
    ("12h", "12 hours"),
    ("day", "Day"),
    ("week", "Week"),
    ("month", "Month"),
]


class QuotaPolicyAdmin(ModelView):
    label = "Quota Policies"
    icon = "fa fa-gauge"

    fields = [
        "id",
        fields.HasOne("user", identity="user", searchable=True, label="User", required=False),
        fields.HasOne("plan", identity="plan",searchable=True, label="Plan", required=False),
        fields.StringField("resource_pattern", required=True),
        fields.IntegerField("limit", required=True),
        fields.EnumField("window", choices=WINDOW_CHOICES, required=True),
        EpochDateTimeField("effective_from", label="Effective From", read_only=True),
        EpochDateTimeField("expires_at", label="Expires At", read_only=True),
    ]

    list_columns = [
        "user", "plan", "resource_pattern", "limit", "window", "effective_from", "expires_at"
    ]

    sortable_fields = ["limit", "effective_from", "expires_at"]
    search_fields = ["resource_pattern", "user_id", "plan_id"]


VIEWS = [QuotaPolicyAdmin(QuotaPolicy)]

