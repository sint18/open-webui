from decimal import Decimal
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import or_

from open_webui.internal.db import get_db
from open_webui.models.billing import PaymentOrder, PaymentStatusEnum
from open_webui.models.users import User
from open_webui.models.affiliate import (
    AttrViaEnum,
    Attribution,
    Commission,
    CommissionStatusEnum,
    CommissionTypeEnum,
    OrderAttribution,
)
from open_webui.utils.auth import get_admin_or_support_user

router = APIRouter()


class CommissionSchema(BaseModel):
    id: str
    partner_id: str
    type: CommissionTypeEnum
    status: CommissionStatusEnum
    amount: Decimal
    created_at: int

    model_config = ConfigDict(from_attributes=True)


class OrderLookupSchema(BaseModel):
    order_id: str
    buyer_id: str
    buyer_email: Optional[str] = None
    amount_mmk: Decimal
    status: PaymentStatusEnum
    partner_id: Optional[str] = None
    via: Optional[AttrViaEnum] = None
    commission: Optional[CommissionSchema] = None
    links: Dict[str, Optional[str]] = {}

    model_config = ConfigDict(from_attributes=True)


@router.get("/order-lookup", response_model=List[OrderLookupSchema])
def order_lookup(
    order_id: Optional[str] = None,
    buyer: Optional[str] = None,
    admin=Depends(get_admin_or_support_user),
):
    if not order_id and not buyer:
        raise HTTPException(status_code=400, detail="order_id or buyer required")

    with get_db() as db:
        query = (
            db.query(
                PaymentOrder,
                User,
                OrderAttribution,
                Attribution,
                Commission,
            )
            .select_from(PaymentOrder)
            .join(User, PaymentOrder.user_id == User.id)
            .outerjoin(
                OrderAttribution, PaymentOrder.order_id == OrderAttribution.order_id
            )
            .outerjoin(Attribution, OrderAttribution.attribution_id == Attribution.id)
            .outerjoin(Commission, PaymentOrder.order_id == Commission.order_id)
        )

        if order_id:
            query = query.filter(PaymentOrder.order_id == order_id)
        if buyer:
            like = f"%{buyer}%"
            query = query.filter(or_(User.email.ilike(like), User.id == buyer))

        rows = query.all()

        results: List[OrderLookupSchema] = []
        for po, user, _oa, attr, comm in rows:
            links: Dict[str, Optional[str]] = {
                "order": f"/admin/settings/orders?order_id={po.order_id}",
                "buyer": f"/admin/users/{po.user_id}",
            }
            partner_id = None
            via = None
            if attr:
                partner_id = attr.partner_id
                via = attr.attr_via
                links["partner"] = f"/admin/affiliate/partners/{attr.partner_id}"
            if comm:
                links["commission"] = (
                    f"/admin/affiliate/commissions?order_id={po.order_id}"
                )

            results.append(
                OrderLookupSchema(
                    order_id=po.order_id,
                    buyer_id=po.user_id,
                    buyer_email=user.email if user else None,
                    amount_mmk=Decimal(po.amount_mmk),
                    status=po.status,
                    partner_id=partner_id,
                    via=via,
                    commission=(
                        CommissionSchema.model_validate(comm, from_attributes=True)
                        if comm
                        else None
                    ),
                    links=links,
                )
            )

        return results
