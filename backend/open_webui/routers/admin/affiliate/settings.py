from decimal import Decimal
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from open_webui.config import CONFIG_DATA, save_config
from open_webui.internal.db import get_db
from open_webui.models.audit import AuditLog
from open_webui.utils.auth import get_admin_or_support_user

router = APIRouter()


class AffiliateSettings(BaseModel):
    cookie_window_days: int
    lock_period_days: int
    min_payout_amount: float
    attribution_model: str
    terms_version: int


@router.get("/settings", response_model=AffiliateSettings)
def get_settings(admin=Depends(get_admin_or_support_user)):
    aff = CONFIG_DATA.get("affiliate", {})
    return AffiliateSettings(
        cookie_window_days=aff.get("cookie_window_days", 30),
        lock_period_days=aff.get("lock_period_days", 30),
        min_payout_amount=aff.get("min_payout_amount", 0),
        attribution_model=aff.get("attribution_model", "last_click"),
        terms_version=aff.get("terms_version", 1),
    )


class AffiliateSettingsForm(BaseModel):
    cookie_window_days: Optional[int] = None
    lock_period_days: Optional[int] = None
    min_payout_amount: Optional[Decimal] = None
    attribution_model: Optional[str] = None
    terms_version: int


@router.put("/settings", response_model=AffiliateSettings)
def update_settings(
    form: AffiliateSettingsForm, admin=Depends(get_admin_or_support_user)
):
    config = CONFIG_DATA.copy()
    aff = config.get("affiliate", {})
    changes: Dict[str, Any] = {}

    if form.cookie_window_days is not None and form.cookie_window_days != aff.get(
        "cookie_window_days"
    ):
        aff["cookie_window_days"] = form.cookie_window_days
        changes["cookie_window_days"] = form.cookie_window_days

    if form.lock_period_days is not None and form.lock_period_days != aff.get(
        "lock_period_days"
    ):
        aff["lock_period_days"] = form.lock_period_days
        changes["lock_period_days"] = form.lock_period_days

    if form.min_payout_amount is not None and float(form.min_payout_amount) != aff.get(
        "min_payout_amount"
    ):
        aff["min_payout_amount"] = float(form.min_payout_amount)
        changes["min_payout_amount"] = float(form.min_payout_amount)

    if form.attribution_model is not None and form.attribution_model != aff.get(
        "attribution_model"
    ):
        aff["attribution_model"] = form.attribution_model
        changes["attribution_model"] = form.attribution_model

    if form.terms_version != aff.get("terms_version"):
        aff["terms_version"] = form.terms_version
        changes["terms_version"] = form.terms_version

    if changes:
        config["affiliate"] = aff
        save_config(config)
        with get_db() as db:
            db.add(
                AuditLog(
                    action="update_affiliate_settings",
                    severity=AuditSeverityEnum.info,
                    details={"changes": changes, "terms_version": aff["terms_version"]},
                )
            )
            db.commit()
    return AffiliateSettings(
        cookie_window_days=aff.get("cookie_window_days", 30),
        lock_period_days=aff.get("lock_period_days", 30),
        min_payout_amount=aff.get("min_payout_amount", 0),
        attribution_model=aff.get("attribution_model", "last_click"),
        terms_version=aff.get("terms_version", 1),
    )
