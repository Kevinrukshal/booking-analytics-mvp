from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Booking, ErrorRecord, Upload
from app.db.session import get_db
from app.services.excel_parser import parse_workbook

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.get("")
def list_uploads(db: Session = Depends(get_db)):
    uploads = db.scalars(select(Upload).order_by(Upload.created_at.desc())).all()
    return [{"id": item.id, "filename": item.filename, "status": item.status, "createdAt": item.created_at, "bookingCount": item.booking_count, "errorCount": item.error_count, "summary": item.summary} for item in uploads]


@router.post("")
async def upload_workbook(file: UploadFile = File(...), replace: bool = False, db: Session = Depends(get_db)):
    filename = Path(file.filename or "upload.xlsx").name
    if Path(filename).suffix.casefold() != ".xlsx":
        raise HTTPException(415, "Only .xlsx workbooks are supported.")
    content = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"Workbook exceeds the {settings.max_upload_mb} MB limit.")
    if not content.startswith(b"PK"):
        raise HTTPException(400, "The uploaded file is not a valid .xlsx workbook.")
    upload = Upload(filename=filename, status="processing", summary={})
    db.add(upload)
    db.flush()
    try:
        parsed = parse_workbook(content)
        if replace:
            old_ids = list(db.scalars(select(Upload.id).where(Upload.id != upload.id)))
            if old_ids:
                db.execute(delete(ErrorRecord).where(ErrorRecord.upload_id.in_(old_ids)))
                db.execute(delete(Booking).where(Booking.upload_id.in_(old_ids)))
                db.execute(delete(Upload).where(Upload.id.in_(old_ids)))
        db.bulk_insert_mappings(Booking, [{**row, "upload_id": upload.id} for row in parsed.bookings])
        db.bulk_insert_mappings(ErrorRecord, [{**row, "upload_id": upload.id} for row in parsed.errors])
        upload.booking_count = len(parsed.bookings)
        upload.error_count = len(parsed.errors)
        upload.summary = parsed.summary
        upload.status = "completed"
        db.commit()
        db.refresh(upload)
        return {"id": upload.id, "filename": filename, "status": upload.status, "bookingCount": upload.booking_count, "errorCount": upload.error_count, "summary": upload.summary, "aiEnabled": bool(settings.allow_external_ai and settings.gemini_api_key and settings.gemini_model)}
    except ValueError as exc:
        db.rollback()
        raise HTTPException(422, str(exc)) from exc
    except Exception:
        db.rollback()
        raise HTTPException(500, "Import failed. Check the workbook format and database availability.") from None

