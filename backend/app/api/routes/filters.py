from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Booking, ErrorRecord
from app.db.session import get_db
from app.services.analytics import latest_upload

router = APIRouter(prefix="/api/filters", tags=["filters"])


@router.get("")
def filters(db: Session = Depends(get_db)):
    upload = latest_upload(db)
    if not upload: return {}
    def distinct(column):
        return [value for value in db.scalars(select(column).where(column.is_not(None), Booking.upload_id == upload.id).distinct().order_by(column))]
    def error_distinct(column):
        return [value for value in db.scalars(select(column).where(column.is_not(None), ErrorRecord.upload_id == upload.id).distinct().order_by(column))]
    return {"agents": distinct(Booking.agent), "teams": distinct(Booking.team), "bookingStatuses": distinct(Booking.booking_status), "productStatuses": distinct(Booking.product_status), "handledAgents": error_distinct(ErrorRecord.handled_agent), "categories": error_distinct(ErrorRecord.category), "severities": error_distinct(ErrorRecord.severity)}

