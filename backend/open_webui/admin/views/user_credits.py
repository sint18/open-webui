from __future__ import annotations

from starlette_admin import fields
from starlette_admin.contrib.sqla import ModelView

from open_webui.admin.fields import EpochDateTimeField
from open_webui.models.billing import UserCredit, StatusEnum


class UserCreditAdmin(ModelView):
    label = "User Credits"
    icon = "fa fa-coins"
    exclude_fields_from_list = ["user_id"]
    fields = [
        "user_id",
        fields.HasOne("user", searchable=True, label="User", required=True, identity="user"),
        fields.HasOne("plan", searchable=True, label="Plan", required=True, identity="plan"),
        fields.IntegerField("credit_balance", required=True),
        fields.IntegerField("image_credit_balance", required=False),
        fields.IntegerField("video_credit_balance", required=False),
        fields.IntegerField("monthly_quota", required=True),
        fields.IntegerField("monthly_image_quota", required=False),
        fields.IntegerField("monthly_video_quota", required=False),
        EpochDateTimeField("current_period_end", label="Current Period End"),
        fields.EnumField("status", enum=StatusEnum, required=True),
        EpochDateTimeField("updated_at", label="Updated", read_only=True),
    ]

    sortable_fields = [
        "credit_balance", "monthly_quota", "updated_at", "status"
    ]

    search_fields = ["user_id", "plan_id"]


VIEWS = [UserCreditAdmin(UserCredit)]

