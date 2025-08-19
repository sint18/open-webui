import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from open_webui.internal.db import get_db
from open_webui.models.affiliate import (
    Application,
    FraudFlag,
    ApplicationStatusEnum,
    PartnerProfile,
    PartnerStatusEnum,
)
from open_webui.utils.auth import get_admin_or_support_user

router = APIRouter()


class ApplicationSchema(BaseModel):
    id: str
    partner_id: str
    status: ApplicationStatusEnum
    notes: Optional[str] = None
    created_at: int
    updated_at: int
    fraud_flags: List[str] = []

    model_config = ConfigDict(from_attributes=True)


@router.get("/applications", response_model=List[ApplicationSchema])
def list_applications(
    status: Optional[ApplicationStatusEnum] = None,
    flagged: bool = False,
    admin=Depends(get_admin_or_support_user),
):
    with get_db() as db:
        query = db.query(Application)
        if status:
            query = query.filter(Application.status == status)
        records = query.order_by(Application.created_at.desc()).all()
        results: List[ApplicationSchema] = []
        for r in records:
            flags = [
                f.flag_type
                for f in db.query(FraudFlag).filter(FraudFlag.partner_id == r.partner_id)
            ]
            if flagged and not flags:
                continue
            app = ApplicationSchema.model_validate(r, from_attributes=True)
            app.fraud_flags = flags
            results.append(app)
        return results


@router.get("/applications/{app_id}", response_model=ApplicationSchema)
def get_application(app_id: str, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        record = db.get(Application, app_id)
        if not record:
            raise HTTPException(status_code=404, detail="Application not found")
        app = ApplicationSchema.model_validate(record, from_attributes=True)
        app.fraud_flags = [
            f.flag_type
            for f in db.query(FraudFlag).filter(FraudFlag.partner_id == record.partner_id)
        ]
        return app


@router.post("/applications/{app_id}/approve")
def approve_application(app_id: str, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        record = db.get(Application, app_id)
        if not record:
            raise HTTPException(status_code=404, detail="Application not found")
        record.status = ApplicationStatusEnum.approved
        record.updated_at = int(time.time())
        profile = db.get(PartnerProfile, record.partner_id)
        if profile:
            profile.status = PartnerStatusEnum.active
            profile.updated_at = int(time.time())
        else:
            profile = PartnerProfile(
                partner_id=record.partner_id,
                status=PartnerStatusEnum.active,
                created_at=int(time.time()),
                updated_at=int(time.time()),
            )
            db.add(profile)
        db.commit()
    return {"id": app_id, "status": "approved"}


class ApplicationRejectForm(BaseModel):
    note: str


@router.post("/applications/{app_id}/reject")
def reject_application(app_id: str, form: ApplicationRejectForm, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        record = db.get(Application, app_id)
        if not record:
            raise HTTPException(status_code=404, detail="Application not found")
        record.status = ApplicationStatusEnum.rejected
        record.updated_at = int(time.time())
        record.notes = form.note
        db.commit()
    return {"id": app_id, "status": "rejected"}


@router.post("/applications/{app_id}/flags/review")
def review_application_flags(app_id: str, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        record = db.get(Application, app_id)
        if not record:
            raise HTTPException(status_code=404, detail="Application not found")
        db.query(FraudFlag).filter(FraudFlag.partner_id == record.partner_id).delete()
        db.commit()
    return {"id": app_id, "flags_cleared": True}
