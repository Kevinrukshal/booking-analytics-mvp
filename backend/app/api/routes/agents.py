from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Booking, ErrorRecord
from app.db.session import get_db
from app.services.analytics import agent_metrics, booking_dict, error_counts, latest_upload

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("")
def agents(search: str | None = None, team: str | None = None, min_bookings: int = Query(0, alias="minBookings", ge=0), db: Session = Depends(get_db)):
    upload = latest_upload(db)
    if not upload: return {"items": [], "overallErrorRate": 0, "minimumRankingBookings": 10}
    bookings = list(db.scalars(select(Booking).where(Booking.upload_id == upload.id)))
    errors = list(db.scalars(select(ErrorRecord).where(ErrorRecord.upload_id == upload.id)))
    items = agent_metrics(bookings, errors)
    if search: items = [item for item in items if search.casefold() in item["agent"].casefold()]
    if team: items = [item for item in items if item["team"] == team]
    items = [item for item in items if item["bookings"] >= min_bookings]
    total_error_bookings = sum(item["errorBookings"] for item in agent_metrics(bookings, errors))
    return {"items": items, "overallErrorRate": total_error_bookings / len(bookings) if bookings else 0, "minimumRankingBookings": 10}


@router.get("/{agent}")
def agent_detail(agent: str, db: Session = Depends(get_db)):
    upload = latest_upload(db)
    if not upload: raise HTTPException(404, "No workbook uploaded.")
    all_bookings = list(db.scalars(select(Booking).where(Booking.upload_id == upload.id)))
    bookings = [row for row in all_bookings if row.agent == agent]
    if not bookings: raise HTTPException(404, "Agent not found.")
    errors = list(db.scalars(select(ErrorRecord).where(ErrorRecord.upload_id == upload.id)))
    metric = next(item for item in agent_metrics(all_bookings, errors) if item["agent"] == agent)
    counts = error_counts(errors)
    categories: dict[str, int] = {}
    refs = {row.booking_reference for row in bookings}
    for error in errors:
        if error.booking_reference in refs:
            category = error.ai_category or error.category
            categories[category] = categories.get(category, 0) + 1
    problem = sorted(bookings, key=lambda row: (counts.get(row.booking_reference, {}).get("open", 0), counts.get(row.booking_reference, {}).get("errors", 0)), reverse=True)
    return {"agent": metric, "errorBreakdown": [{"category": key, "value": value} for key, value in sorted(categories.items(), key=lambda item: -item[1])], "bookings": [booking_dict(row, counts) for row in problem[:25]]}
