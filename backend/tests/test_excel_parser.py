# All names, identifiers and amounts below are fictional test fixtures.
from io import BytesIO

from openpyxl import Workbook

from app.services.excel_parser import parse_workbook


def workbook_bytes() -> bytes:
    workbook = Workbook()
    bookings = workbook.active
    bookings.title = "Bookings"
    bookings.append(["Booking Ref", "Date", "Travel Date", "Agent", "Team", "Selling Cost", "Profit", "Product Status", "Pending Products"])
    bookings.append([1000001, "2026-08-01", "2026-09-01", " demo agent ", "Demo Team", 1000, 150, "Pending", "Hotel"])
    bookings.append([1000001, "2026-08-02", "2026-09-02", "DEMO AGENT", "Demo Team", 1100, 175, "Booked", None])
    bookings.append([None, "2026-08-02", None, "Demo Operator", "Demo Team", 500, 50, "Booked", None])
    errors = workbook.create_sheet("Errors")
    errors.append(["Booking Reference", "Issue Found", "Status", "Responsible Agent", "Handled Agent"])
    errors.append([1000001, "Pax name entered wrong in PNR", "Pending", "Demo Agent", "Demo Agent"])
    errors.append([9999999, "Voucher not attached", "Sorted", "Demo Operator", "Demo Handler"])
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def test_booking_error_join_and_duplicate_detection():
    parsed = parse_workbook(workbook_bytes())
    assert len(parsed.bookings) == 1
    assert parsed.bookings[0]["booking_reference"] == "1000001"
    assert parsed.bookings[0]["agent"] == "Demo Agent"
    assert len(parsed.bookings[0]["raw_data"]["source_rows"]) == 2
    assert parsed.summary["missing_booking_references"] == 1
    assert parsed.summary["duplicate_booking_references_merged"] == 1
    assert parsed.summary["matched_error_rows"] == 1
    assert parsed.summary["unmatched_error_rows"] == 1


def test_full_year_workbook_keeps_january_and_december_rows():
    workbook = Workbook()
    bookings = workbook.active
    bookings.title = "Bookings 2026"
    bookings.append(["Booking Reference", "Date", "Travel Date", "Agent", "Team", "Selling Cost"])
    bookings.append(["JAN001", "2026-01-04", "2026-02-10", "Alex", "North", 1200])
    bookings.append(["DEC001", "2026-12-18", "2027-01-12", "Demo Operator", "South", 2400])
    errors = workbook.create_sheet("Errors 2026")
    errors.append(["Booking Reference", "Issue Found", "Status"])
    errors.append(["JAN001", "Voucher missing", "Sorted"])
    errors.append(["DEC001", "Passenger name needs correction", "Pending"])
    output = BytesIO()
    workbook.save(output)

    parsed = parse_workbook(output.getvalue())

    assert len(parsed.bookings) == 2
    assert {row["booking_date"].month for row in parsed.bookings} == {1, 12}
    assert parsed.summary["matched_error_rows"] == 2
