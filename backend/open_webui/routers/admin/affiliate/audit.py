from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from open_webui.internal.db import get_db
from open_webui.models.audit import AuditLog
from open_webui.utils.auth import get_admin_or_support_user

router = APIRouter()


class AuditLogSchema(BaseModel):
    id: str
    actor_id: str
    resource: str
    action: str
    before: dict | None = None
    after: dict | None = None
    reason: str | None = None
    timestamp: int

    model_config = ConfigDict(from_attributes=True)


@router.get("/audit", response_model=List[AuditLogSchema])
def list_audit_logs(
    actor_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
    start: Optional[int] = None,
    end: Optional[int] = None,
    admin=Depends(get_admin_or_support_user),
):
    with get_db() as db:
        query = db.query(AuditLog)
        if actor_id:
            query = query.filter(AuditLog.actor_id == actor_id)
        if resource_type:
            query = query.filter(AuditLog.resource.like(f"{resource_type}:%"))
        if action:
            query = query.filter(AuditLog.action == action)
        if start:
            query = query.filter(AuditLog.timestamp >= start)
        if end:
            query = query.filter(AuditLog.timestamp <= end)
        logs = query.order_by(AuditLog.timestamp.desc()).all()
        return [AuditLogSchema.model_validate(l, from_attributes=True) for l in logs]


@router.get("/audit/{log_id}/diff")
def get_audit_diff(log_id: str, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        log = db.get(AuditLog, log_id)
        if not log:
            raise HTTPException(status_code=404, detail="Audit log not found")
        before = log.before or {}
        after = log.after or {}
        diff = {}
        keys = set(before.keys()) | set(after.keys())
        for k in keys:
            if before.get(k) != after.get(k):
                diff[k] = {"before": before.get(k), "after": after.get(k)}
        return {"id": log_id, "diff": diff}
