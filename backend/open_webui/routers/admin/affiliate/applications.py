import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import or_

from open_webui.internal.db import get_db
from open_webui.models.affiliate import (
    Application,
    FraudFlag,
    ApplicationStatusEnum,
    PartnerProfile,
    PartnerStatusEnum,
    Link,
    DiscountCodeBinding,
)
from open_webui.models.audit import AuditLog
from open_webui.models.discount import DiscountCode
from open_webui.models.users import User
from open_webui.utils.auth import get_admin_or_support_user

router = APIRouter()


PAGE_ITEM_COUNT = 50


class ApplicationSchema(BaseModel):
    id: str
    partner_id: str
    name: str = ""
    email: str = ""
    status: ApplicationStatusEnum
    notes: Optional[str] = None
    created_at: int
    updated_at: int
    fraud_flags: List[str] = []

    model_config = ConfigDict(from_attributes=True)


@router.get("/applications", response_model=List[ApplicationSchema])
def list_applications(
    status: Optional[ApplicationStatusEnum] = None,
    from_ts: Optional[int] = Query(None, alias="from"),
    to_ts: Optional[int] = Query(None, alias="to"),
    q: Optional[str] = None,
    page: Optional[int] = 1,
    flagged: bool = False,
    admin=Depends(get_admin_or_support_user),
):
    limit = PAGE_ITEM_COUNT
    page = max(1, page)
    skip = (page - 1) * limit
    with get_db() as db:
        query = (
            db.query(Application, User.name, User.email)
            .join(User, User.id == Application.partner_id)
        )
        if status:
            query = query.filter(Application.status == status)
        if from_ts:
            query = query.filter(Application.created_at >= from_ts)
        if to_ts:
            query = query.filter(Application.created_at <= to_ts)
        if q:
            like = f"%{q}%"
            query = query.filter(or_(User.name.ilike(like), User.email.ilike(like)))
        records = (
            query.order_by(Application.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        results: List[ApplicationSchema] = []
        for r, name, email in records:
            flags = [
                f.flag_type
                for f in db.query(FraudFlag).filter(FraudFlag.partner_id == r.partner_id)
            ]
            if flagged and not flags:
                continue
            app = ApplicationSchema.model_validate(r, from_attributes=True)
            app.name = name
            app.email = email
            app.fraud_flags = flags
            results.append(app)
        return results


@router.get("/applications/{app_id}", response_model=ApplicationSchema)
def get_application(app_id: str, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        record = db.get(Application, app_id)
        if not record:
            raise HTTPException(status_code=404, detail="Application not found")
        user = db.get(User, record.partner_id)
        app = ApplicationSchema.model_validate(record, from_attributes=True)
        app.name = user.name if user else ""
        app.email = user.email if user else ""
        app.fraud_flags = [
            f.flag_type
            for f in db.query(FraudFlag).filter(FraudFlag.partner_id == record.partner_id)
        ]
        return app


class ApplicationApproveForm(BaseModel):
    link_code: str
    link_url: str
    coupon_code: Optional[str] = None
    coupon_discount_percent: Optional[int] = None
    coupon_expires_at: Optional[int] = None


@router.post("/applications/{app_id}/approve")
def approve_application(
    app_id: str,
    form: ApplicationApproveForm,
    admin=Depends(get_admin_or_support_user),
):
    with get_db() as db:
        record = db.get(Application, app_id)
        if not record:
            raise HTTPException(status_code=404, detail="Application not found")
        before = ApplicationSchema.model_validate(record, from_attributes=True).model_dump()

        if db.query(Link).filter(Link.code == form.link_code).first():
            raise HTTPException(status_code=400, detail="Link code already exists")

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

        link = Link(partner_id=record.partner_id, code=form.link_code, url=form.link_url)
        db.add(link)

        if form.coupon_code:
            if db.query(DiscountCode).filter(DiscountCode.code == form.coupon_code).first():
                raise HTTPException(status_code=400, detail="Discount code already exists")
            discount = DiscountCode(
                code=form.coupon_code,
                discount_percent=form.coupon_discount_percent,
                expires_at=form.coupon_expires_at,
            )
            db.add(discount)
            binding = DiscountCodeBinding(
                partner_id=record.partner_id,
                code=form.coupon_code,
                expires_at=form.coupon_expires_at,
            )
            db.add(binding)

        after = ApplicationSchema.model_validate(record, from_attributes=True).model_dump()
        db.add(
            AuditLog(
                actor_id=admin.id,
                resource=f"application:{app_id}",
                action="approve_application",
                before=before,
                after=after,
                reason=None,
            )
        )

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
        before = ApplicationSchema.model_validate(record, from_attributes=True).model_dump()
        record.status = ApplicationStatusEnum.rejected
        record.updated_at = int(time.time())
        record.notes = form.note
        after = ApplicationSchema.model_validate(record, from_attributes=True).model_dump()
        db.add(
            AuditLog(
                actor_id=admin.id,
                resource=f"application:{app_id}",
                action="reject_application",
                before=before,
                after=after,
                reason=form.note,
            )
        )
        db.commit()
    return {"id": app_id, "status": "rejected"}


@router.post("/applications/{app_id}/flags/review")
def review_application_flags(app_id: str, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        record = db.get(Application, app_id)
        if not record:
            raise HTTPException(status_code=404, detail="Application not found")
        flags = [f.flag_type for f in db.query(FraudFlag).filter(FraudFlag.partner_id == record.partner_id)]
        db.query(FraudFlag).filter(FraudFlag.partner_id == record.partner_id).delete()
        db.add(
            AuditLog(
                actor_id=admin.id,
                resource=f"application:{app_id}",
                action="review_application_flags",
                before={"flags": flags},
                after={"flags": []},
                reason=None,
            )
        )
        db.commit()
    return {"id": app_id, "flags_cleared": True}
