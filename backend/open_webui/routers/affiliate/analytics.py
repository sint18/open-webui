from collections import defaultdict
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from open_webui.internal.db import get_db
from open_webui.models.affiliate import Click, Attribution, Commission
from open_webui.utils.auth import get_verified_user

router = APIRouter()


class TimeseriesItem(BaseModel):
    day: int
    clicks: int
    attributions: int
    commissions: Decimal


@router.get("/analytics/timeseries", response_model=List[TimeseriesItem])
def analytics_timeseries(user=Depends(get_verified_user)):
    """Return aggregated affiliate metrics grouped by day."""
    data: dict[int, dict[str, Decimal | int]] = defaultdict(
        lambda: {"clicks": 0, "attributions": 0, "commissions": Decimal("0")}
    )
    with get_db() as db:
        for row in db.query(Click).filter(Click.partner_id == user.id).all():
            day = row.created_at - row.created_at % 86400
            data[day]["clicks"] += 1
        for row in db.query(Attribution).filter(Attribution.partner_id == user.id).all():
            day = row.created_at - row.created_at % 86400
            data[day]["attributions"] += 1
        for row in db.query(Commission).filter(Commission.partner_id == user.id).all():
            day = row.created_at - row.created_at % 86400
            data[day]["commissions"] += Decimal(row.amount)
    results: List[TimeseriesItem] = []
    for day, values in sorted(data.items()):
        results.append(
            TimeseriesItem(
                day=day,
                clicks=int(values["clicks"]),
                attributions=int(values["attributions"]),
                commissions=Decimal(values["commissions"]),
            )
        )
    return results
