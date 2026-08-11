from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import Booking, ErrorRecord
from app.db.session import get_db
from app.services.analytics import booking_dict, error_counts, error_dict, latest_upload

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


@router.get("")
def bookings(
    search: str | None = None, agent: str | None = None, team: str | None = None,
    booking_status: str | None = None, product_status: str | None = None,
    has_errors: bool | None = Query(None, alias="hasErrors"), pending_product: bool | None = Query(None, alias="pendingProduct"),
    date_from: date | None = Query(None, alias="dateFrom"), date_to: date | None = Query(None, alias="dateTo"),
    page: int = Query(1, ge=1), page_size: int = Query(25, alias="pageSize", ge=1, le=100),
    db: Session = Depends(get_db),
):
    upload = latest_upload(db)
    if not upload:
        return {"items": [], "total": 0, "page": page, "pageSize": page_size}
    stmt = select(Booking).where(Booking.upload_id == upload.id)
    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(or_(Booking.booking_reference.ilike(term), Booking.agent.ilike(term), Booking.team.ilike(term)))
    if agent: stmt = stmt.where(Booking.agent == agent)
    if team: stmt = stmt.where(Booking.team == team)
    if booking_status: stmt = stmt.where(Booking.booking_status == booking_status)
    if product_status: stmt = stmt.where(Booking.product_status == product_status)
    if pending_product is True: stmt = stmt.where(or_(Booking.pending_products.is_not(None), Booking.product_status.ilike("pending")))
    if date_from: stmt = stmt.where(Booking.travel_date >= date_from)
    if date_to: stmt = stmt.where(Booking.travel_date <= date_to)
    rows = list(db.scalars(stmt.order_by(Booking.booking_date.desc(), Booking.booking_reference)))
    all_errors = list(db.scalars(select(ErrorRecord).where(ErrorRecord.upload_id == upload.id)))
    counts = error_counts(all_errors)
    if has_errors is not None:
        rows = [row for row in rows if (counts.get(row.booking_reference, {}).get("errors", 0) > 0) is has_errors]
    total = len(rows)
    start = (page - 1) * page_size
    return {"items": [booking_dict(row, counts) for row in rows[start:start + page_size]], "total": total, "page": page, "pageSize": page_size}


@router.get("/{booking_reference}")
def booking_detail(booking_reference: str, db: Session = Depends(get_db)):
    upload = latest_upload(db)
    if not upload:
        raise HTTPException(404, "No workbook uploaded.")
    booking = db.scalar(select(Booking).where(Booking.upload_id == upload.id, Booking.booking_reference == booking_reference.upper()))
    if not booking:
        raise HTTPException(404, "Booking not found.")
    errors = list(db.scalars(select(ErrorRecord).where(ErrorRecord.upload_id == upload.id, ErrorRecord.booking_reference == booking.booking_reference).order_by(ErrorRecord.issue_date.desc().nullslast(), ErrorRecord.id.desc())))
    return {**booking_dict(booking, error_counts(errors)), "errors": [error_dict(error, True) for error in errors], "rawData": booking.raw_data}

