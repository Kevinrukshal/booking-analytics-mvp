from datetime import date
from datetime import datetime
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Booking, ErrorRecord
from app.db.session import get_db
from app.services.analytics import error_dict, latest_upload
from app.services.export_workbook import build_errors_export

router = APIRouter(prefix="/api/errors", tags=["errors"])


def _filtered_errors(
    db: Session,
    status: str | None = None,
    agent: str | None = None,
    handled_agent: str | None = None,
    category: str | None = None,
    severity: str | None = None,
    booking_reference: str | None = None,
    matched: bool | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    selected_ids: set[int] | None = None,
) -> tuple[list[ErrorRecord], set[str]]:
    upload = latest_upload(db)
    if not upload:
        return [], set()
    stmt = select(ErrorRecord).where(ErrorRecord.upload_id == upload.id)
    if selected_ids:
        stmt = stmt.where(ErrorRecord.id.in_(selected_ids))
    if status:
        stmt = stmt.where(ErrorRecord.status != "resolved" if status == "open" else ErrorRecord.status == status)
    if agent:
        stmt = stmt.where(ErrorRecord.responsible_agent == agent)
    if handled_agent:
        stmt = stmt.where(ErrorRecord.handled_agent == handled_agent)
    if category:
        stmt = stmt.where((ErrorRecord.ai_category == category) | (ErrorRecord.category == category))
    if severity:
        stmt = stmt.where((ErrorRecord.ai_severity == severity) | (ErrorRecord.severity == severity))
    if booking_reference:
        stmt = stmt.where(ErrorRecord.booking_reference.ilike(f"%{booking_reference}%"))
    if date_from:
        stmt = stmt.where(ErrorRecord.issue_date >= date_from)
    if date_to:
        stmt = stmt.where(ErrorRecord.issue_date <= date_to)
    rows = list(db.scalars(stmt.order_by(ErrorRecord.issue_date.desc().nullslast(), ErrorRecord.id.desc())))
    booking_refs = set(db.scalars(select(Booking.booking_reference).where(Booking.upload_id == upload.id)))
    if matched is not None:
        rows = [row for row in rows if (row.booking_reference in booking_refs) is matched]
    return rows, booking_refs


def _selected_ids(ids: str | None) -> set[int] | None:
    if not ids:
        return None
    try:
        return {int(value) for value in ids.split(",") if value.strip()}
    except ValueError as exc:
        raise HTTPException(422, "Selected error IDs must be numbers.") from exc


@router.get("")
def errors(
    status: str | None = None, agent: str | None = None, handled_agent: str | None = Query(None, alias="handledAgent"),
    category: str | None = None, severity: str | None = None, booking_reference: str | None = Query(None, alias="bookingReference"),
    matched: bool | None = None, date_from: date | None = Query(None, alias="dateFrom"), date_to: date | None = Query(None, alias="dateTo"),
    page: int = Query(1, ge=1), page_size: int = Query(25, alias="pageSize", ge=1, le=100), db: Session = Depends(get_db),
):
    rows, booking_refs = _filtered_errors(
        db, status, agent, handled_agent, category, severity, booking_reference,
        matched, date_from, date_to,
    )
    total = len(rows); start = (page - 1) * page_size
    return {"items": [error_dict(row, row.booking_reference in booking_refs) for row in rows[start:start + page_size]], "total": total, "page": page, "pageSize": page_size}


@router.get("/export")
def export_errors(
    status: str | None = None, agent: str | None = None, handled_agent: str | None = Query(None, alias="handledAgent"),
    category: str | None = None, severity: str | None = None, booking_reference: str | None = Query(None, alias="bookingReference"),
    matched: bool | None = None, date_from: date | None = Query(None, alias="dateFrom"), date_to: date | None = Query(None, alias="dateTo"),
    ids: str | None = None, db: Session = Depends(get_db),
):
    selected_ids = _selected_ids(ids)
    rows, _ = _filtered_errors(
        db, status, agent, handled_agent, category, severity, booking_reference,
        matched, date_from, date_to, selected_ids,
    )
    content = build_errors_export(rows)
    filename = f"booking-analytics-errors-{datetime.now():%Y%m%d-%H%M}.xlsx"
    return StreamingResponse(
        BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
