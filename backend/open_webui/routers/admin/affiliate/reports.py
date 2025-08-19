from decimal import Decimal
from typing import Any, Dict, List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from open_webui.internal.db import get_db
from open_webui.models.affiliate import Commission
from open_webui.models.audit import AuditLog
from open_webui.utils.auth import get_admin_or_support_user
from open_webui.config import CONFIG_DATA, save_config

router = APIRouter()


class RollupRow(BaseModel):
    partner_id: str
    total: Decimal


@router.get("/reports/rollup", response_model=List[RollupRow])
def rollup_report(status: Optional[str] = None, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        query = db.query(Commission.partner_id, func.sum(Commission.amount))
        if status:
            query = query.filter(Commission.status == status)
        rows = query.group_by(Commission.partner_id).all()
        return [RollupRow(partner_id=r[0], total=r[1] or 0) for r in rows]


@router.get("/settings")
def get_settings(admin=Depends(get_admin_or_support_user)):
    return CONFIG_DATA.get("affiliate", {})


class AffiliateSettingsForm(BaseModel):
    commission_rules: Dict[str, Any] | None = None
    lock_period_days: int | None = None
    attribution_policy: str | None = None
    cookie_window_days: int | None = None


@router.put("/settings")
def update_settings(form: AffiliateSettingsForm, admin=Depends(get_admin_or_support_user)):
    config = CONFIG_DATA.copy()
    before = config.get("affiliate", {}).copy()
    aff = config.get("affiliate", {})
    if form.commission_rules is not None:
        aff["commission_rules"] = form.commission_rules
    if form.lock_period_days is not None:
        aff["lock_period_days"] = form.lock_period_days
    if form.attribution_policy is not None:
        aff["attribution_policy"] = form.attribution_policy
    if form.cookie_window_days is not None:
        aff["cookie_window_days"] = form.cookie_window_days
    config["affiliate"] = aff
    save_config(config)
    with get_db() as db:
        db.add(
            AuditLog(
                actor_id=admin.id,
                resource="affiliate:settings",
                action="update_settings",
                before=before,
                after=aff,
                reason=None,
            )
        )
        db.commit()
    return aff
