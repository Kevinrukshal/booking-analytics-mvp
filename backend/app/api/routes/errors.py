from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Booking, ErrorRecord
from app.db.session import get_db
from app.services.analytics import error_dict, latest_upload

router = APIRouter(prefix="/api/errors", tags=["errors"])


@router.get("")
def errors(
    status: str | None = None, agent: str | None = None, handled_agent: str | None = Query(None, alias="handledAgent"),
    category: str | None = None, severity: str | None = None, booking_reference: str | None = Query(None, alias="bookingReference"),
    matched: bool | None = None, date_from: date | None = Query(None, alias="dateFrom"), date_to: date | None = Query(None, alias="dateTo"),
    page: int = Query(1, ge=1), page_size: int = Query(25, alias="pageSize", ge=1, le=100), db: Session = Depends(get_db),
):
    upload = latest_upload(db)
    if not upload: return {"items": [], "total": 0, "page": page, "pageSize": page_size}
    stmt = select(ErrorRecord).where(ErrorRecord.upload_id == upload.id)
    if status:
        stmt = stmt.where(ErrorRecord.status != "resolved" if status == "open" else ErrorRecord.status == status)
    if agent: stmt = stmt.where(ErrorRecord.responsible_agent == agent)
    if handled_agent: stmt = stmt.where(ErrorRecord.handled_agent == handled_agent)
    if category: stmt = stmt.where((ErrorRecord.ai_category == category) | (ErrorRecord.category == category))
    if severity: stmt = stmt.where((ErrorRecord.ai_severity == severity) | (ErrorRecord.severity == severity))
    if booking_reference: stmt = stmt.where(ErrorRecord.booking_reference.ilike(f"%{booking_reference}%"))
    if date_from: stmt = stmt.where(ErrorRecord.issue_date >= date_from)
    if date_to: stmt = stmt.where(ErrorRecord.issue_date <= date_to)
    rows = list(db.scalars(stmt.order_by(ErrorRecord.issue_date.desc().nullslast(), ErrorRecord.id.desc())))
    booking_refs = set(db.scalars(select(Booking.booking_reference).where(Booking.upload_id == upload.id)))
    if matched is not None: rows = [row for row in rows if (row.booking_reference in booking_refs) is matched]
    total = len(rows); start = (page - 1) * page_size
    return {"items": [error_dict(row, row.booking_reference in booking_refs) for row in rows[start:start + page_size]], "total": total, "page": page, "pageSize": page_size}

