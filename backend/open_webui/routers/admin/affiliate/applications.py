import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from open_webui.internal.db import get_db
from open_webui.models.affiliate import Application
from open_webui.utils.auth import get_admin_or_support_user

router = APIRouter()


class ApplicationSchema(BaseModel):
    id: str
    partner_id: str
    status: str
    notes: Optional[str] = None
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


@router.get("/applications", response_model=List[ApplicationSchema])
def list_applications(
    status: Optional[str] = None, admin=Depends(get_admin_or_support_user)
):
    with get_db() as db:
        query = db.query(Application)
        if status:
            query = query.filter(Application.status == status)
        records = query.order_by(Application.created_at.desc()).all()
        return [ApplicationSchema.model_validate(r, from_attributes=True) for r in records]


@router.get("/applications/{app_id}", response_model=ApplicationSchema)
def get_application(app_id: str, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        record = db.get(Application, app_id)
        if not record:
            raise HTTPException(status_code=404, detail="Application not found")
        return ApplicationSchema.model_validate(record, from_attributes=True)


@router.post("/applications/{app_id}/approve")
def approve_application(app_id: str, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        record = db.get(Application, app_id)
        if not record:
            raise HTTPException(status_code=404, detail="Application not found")
        record.status = "approved"
        record.updated_at = int(time.time())
        db.commit()
    return {"id": app_id, "status": "approved"}


@router.post("/applications/{app_id}/reject")
def reject_application(app_id: str, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        record = db.get(Application, app_id)
        if not record:
            raise HTTPException(status_code=404, detail="Application not found")
        record.status = "rejected"
        record.updated_at = int(time.time())
        db.commit()
    return {"id": app_id, "status": "rejected"}
