from datetime import date
from decimal import Decimal
from io import BytesIO

from openpyxl import load_workbook

from app.db.models import Booking, ErrorRecord
from app.services.export_workbook import build_bookings_export, build_errors_export


def test_booking_export_is_formatted_and_typed():
    booking = Booking(
        id=12,
        upload_id=1,
        booking_reference="ABC123",
        booking_date=date(2026, 8, 1),
        travel_date=date(2026, 9, 2),
        agent="Alex",
        team="Elite",
        selling_cost=Decimal("1250.50"),
        profit=Decimal("175.25"),
        product_status="Booked",
        quality_checks={},
        raw_data={},
    )
    content = build_bookings_export([booking])
    workbook = load_workbook(BytesIO(content))
    sheet = workbook["Bookings"]

    assert sheet["A1"].value == "Booking Reference"
    assert sheet["A2"].value == "ABC123"
    assert sheet["B2"].value.date() == date(2026, 8, 1)
    assert sheet["G2"].value == 1250.5
    assert sheet["G2"].number_format == "£#,##0.00"
    assert sheet["R2"].value == "Booked"
    assert sheet.freeze_panes == "A2"
    assert sheet.auto_filter.ref == "A1:Y2"
    assert len(sheet.tables) == 0


def test_error_export_includes_match_state():
    error = ErrorRecord(
        id=7,
        upload_id=1,
        booking_reference="ABC123",
        issue_date=date(2026, 8, 3),
        issue_text="Passenger name needs correction",
        normalized_issue="passenger name needs correction",
        issue_hash="hash",
        status="open",
        responsible_agent="Alex",
        category="Booking Data",
        severity="High",
        raw_data={},
    )
    content = build_errors_export([error])
    workbook = load_workbook(BytesIO(content))
    sheet = workbook["Errors"]

    assert sheet["D2"].value == "Passenger name needs correction"
    assert sheet["G2"].value == "open"
    assert sheet.auto_filter.ref == "A1:J2"
