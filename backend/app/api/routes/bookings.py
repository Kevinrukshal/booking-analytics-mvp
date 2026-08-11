from datetime import date
from datetime import datetime
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import Booking, ErrorRecord
from app.db.session import get_db
from app.services.analytics import booking_dict, error_counts, error_dict, latest_upload
from app.services.export_workbook import build_bookings_export

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


def _filtered_bookings(
    db: Session,
    search: str | None = None,
    agent: str | None = None,
    team: str | None = None,
    booking_status: str | None = None,
    product_status: str | None = None,
    has_errors: bool | None = None,
    pending_product: bool | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    selected_ids: set[int] | None = None,
) -> tuple[list[Booking], dict[str, dict[str, int]]]:
    upload = latest_upload(db)
    if not upload:
        return [], {}
    stmt = select(Booking).where(Booking.upload_id == upload.id)
    if selected_ids:
        stmt = stmt.where(Booking.id.in_(selected_ids))
    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(or_(Booking.booking_reference.ilike(term), Booking.agent.ilike(term), Booking.team.ilike(term)))
    if agent:
        stmt = stmt.where(Booking.agent == agent)
    if team:
        stmt = stmt.where(Booking.team == team)
    if booking_status:
        stmt = stmt.where(Booking.booking_status == booking_status)
    if product_status:
        stmt = stmt.where(Booking.product_status == product_status)
    if pending_product is True:
        stmt = stmt.where(or_(Booking.pending_products.is_not(None), Booking.product_status.ilike("pending")))
    if date_from:
        stmt = stmt.where(Booking.travel_date >= date_from)
    if date_to:
        stmt = stmt.where(Booking.travel_date <= date_to)
    rows = list(db.scalars(stmt.order_by(Booking.booking_date.desc(), Booking.booking_reference)))
    all_errors = list(db.scalars(select(ErrorRecord).where(ErrorRecord.upload_id == upload.id)))
    counts = error_counts(all_errors)
    if has_errors is not None:
        rows = [row for row in rows if (counts.get(row.booking_reference, {}).get("errors", 0) > 0) is has_errors]
    return rows, counts


def _selected_ids(ids: str | None) -> set[int] | None:
    if not ids:
        return None
    try:
        return {int(value) for value in ids.split(",") if value.strip()}
    except ValueError as exc:
        raise HTTPException(422, "Selected booking IDs must be numbers.") from exc


@router.get("")
def bookings(
    search: str | None = None, agent: str | None = None, team: str | None = None,
    booking_status: str | None = None, product_status: str | None = None,
    has_errors: bool | None = Query(None, alias="hasErrors"), pending_product: bool | None = Query(None, alias="pendingProduct"),
    date_from: date | None = Query(None, alias="dateFrom"), date_to: date | None = Query(None, alias="dateTo"),
    page: int = Query(1, ge=1), page_size: int = Query(25, alias="pageSize", ge=1, le=100),
    db: Session = Depends(get_db),
):
    rows, counts = _filtered_bookings(
        db, search, agent, team, booking_status, product_status, has_errors,
        pending_product, date_from, date_to,
    )
    total = len(rows)
    start = (page - 1) * page_size
    return {"items": [booking_dict(row, counts) for row in rows[start:start + page_size]], "total": total, "page": page, "pageSize": page_size}


@router.get("/export")
def export_bookings(
    search: str | None = None, agent: str | None = None, team: str | None = None,
    booking_status: str | None = None, product_status: str | None = None,
    has_errors: bool | None = Query(None, alias="hasErrors"), pending_product: bool | None = Query(None, alias="pendingProduct"),
    date_from: date | None = Query(None, alias="dateFrom"), date_to: date | None = Query(None, alias="dateTo"),
    ids: str | None = None, db: Session = Depends(get_db),
):
    selected_ids = _selected_ids(ids)
    rows, counts = _filtered_bookings(
        db, search, agent, team, booking_status, product_status, has_errors,
        pending_product, date_from, date_to, selected_ids,
    )
    scope = f"{len(rows):,} selected booking{'s' if len(rows) != 1 else ''}" if selected_ids else f"{len(rows):,} filtered booking{'s' if len(rows) != 1 else ''}"
    content = build_bookings_export(rows, counts, scope)
    filename = f"booking-analytics-bookings-{datetime.now():%Y%m%d-%H%M}.xlsx"
    return StreamingResponse(
        BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
