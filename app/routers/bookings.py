from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas, models
from ..database import get_db
from ..auth import get_current_tenant_flexible

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("", response_model=List[schemas.BookingOut])
def list_bookings(
    channel: Optional[str] = None,
    db: Session = Depends(get_db),
    tenant: models.Tenant = Depends(get_current_tenant_flexible),
):
    q = db.query(models.Booking).filter(models.Booking.tenant_id == tenant.id)
    if channel:
        q = q.filter(models.Booking.channel == channel)
    return q.order_by(models.Booking.created_at.desc()).all()
