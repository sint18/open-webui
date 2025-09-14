# backend/open_webui/admin/views/billing/plan.py
from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import List

from requests import Request
from starlette_admin import action, fields
from starlette_admin.contrib.sqla import ModelView
# from starlette_admin.contrib.sqla import filters as sqla_filters
from open_webui.admin.fields import EpochDateTimeField
from open_webui.internal.db import get_db
from open_webui.models.plans import Plan, PlanTypeEnum  # adjust import path if different


def _fmt_ts(ts: int | None) -> str:
    if not ts:
        return "-"
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")

Plan.__admin_repr__ = lambda self, request: f"{self.name} ({self.plan_type})"

class PlanAdmin(ModelView):
    """
    Admin UI for subscription/package/topup plans.
    - Nice formatting for epoch timestamps
    - Bulk activate/deactivate
    - Duplicate plan helper
    - Basic RBAC hooks (override in your base class if you use one)
    """

    # Sidebar text & icon (Tabler name)
    label = "Plans"
    icon = "fa fa-box-open"

    # Table / form fields
    fields = [
        "id",
        fields.StringField("name", required=True),
        fields.TextAreaField("description"),
        fields.FloatField("price", required=True),
        fields.IntegerField("credits", required=True),
        fields.IntegerField("image_credits", required=False),
        fields.IntegerField("video_credits", required=False),
        fields.EnumField("plan_type", enum=PlanTypeEnum, required=True),
        fields.JSONField("features"),
        fields.BooleanField("is_active"),
        # store as epoch in DB but render nicely via formatters (read-only in form)
        EpochDateTimeField("created_at", label="Created", read_only=True),
        EpochDateTimeField("updated_at", label="Updated", read_only=True),
    ]


    list_columns = [
        "name",
        "plan_type",
        "price",
        "credits",
        "image_credits",
        "video_credits",
        "is_active",
        "created_at",
        "updated_at",
    ]

    sortable_fields = [
        "price", "credits", "image_credits", "video_credits", "is_active",
        "created_at", "updated_at",
    ]

    search_fields = ["name", "description"]

    actions = ["activate", "deactivate", "duplicate"]

    page_size = 25

    #
    # Bulk actions
    #
    @action(
        name="activate",
        text="Activate",
        confirmation="Activate selected plans?",
        submit_btn_text="Activate",
    )
    async def activate(self, request, pks: List[str]):
        with get_db() as db:
            db.query(Plan).filter(Plan.id.in_(pks)).update(
                {Plan.is_active: True, Plan.updated_at: int(time.time())},
                synchronize_session=False,
            )
            db.commit()
        return {"message": f"Activated {len(pks)} plan(s)."}

    @action(
        name="deactivate",
        text="Deactivate",
        confirmation="Deactivate selected plans?",
        submit_btn_text="Deactivate",
    )
    async def deactivate(self, request, pks: List[str]):
        with get_db() as db:
            db.query(Plan).filter(Plan.id.in_(pks)).update(
                {Plan.is_active: False, Plan.updated_at: int(time.time())},
                synchronize_session=False,
            )
            db.commit()
        return {"message": f"Deactivated {len(pks)} plan(s)."}

    @action(
        name="duplicate",
        text="Duplicate",
        confirmation="Create a copy of each selected plan (name gets ' (copy)')?",
        submit_btn_text="Duplicate",
    )
    async def duplicate(self, request, pks: List[str]):
        new_count = 0
        with get_db() as db:
            for pid in pks:
                src: Plan | None = db.query(Plan).filter_by(id=pid).first()
                if not src:
                    continue
                now = int(time.time())
                dup = Plan(
                    id=str(uuid.uuid4()),
                    name=f"{src.name} (copy)",
                    description=src.description,
                    price=src.price,
                    credits=src.credits,
                    image_credits=src.image_credits,
                    video_credits=src.video_credits,
                    plan_type=src.plan_type,
                    features=src.features,
                    is_active=False,  # copies start inactive
                    created_at=now,
                    updated_at=now,
                )
                db.add(dup)
                new_count += 1
            db.commit()
        return {"message": f"Created {new_count} copy/copies."}


# Starlette-Admin auto-registry hook
VIEWS = [PlanAdmin(Plan)]
