from decimal import Decimal
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func

from open_webui.internal.db import get_db
from open_webui.models.affiliate import Commission
from open_webui.models.audit import AuditLog
from open_webui.utils.auth import get_admin_or_support_user

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


