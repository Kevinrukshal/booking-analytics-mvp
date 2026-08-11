from __future__ import annotations

from decimal import Decimal
from io import BytesIO
from typing import Any, Iterable

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from app.db.models import Booking, ErrorRecord


HEADER_FILL = PatternFill("solid", fgColor="355E52")
ROW_FILL = PatternFill("solid", fgColor="E2F0D9")
ALT_FILL = PatternFill("solid", fgColor="F5FAF3")
GRID = Side(style="thin", color="6B766F")


def _build_workbook(
    title: str,
    headers: list[str],
    rows: Iterable[list[Any]],
    widths: list[int],
    date_columns: set[int] | None = None,
    currency_columns: set[int] | None = None,
    wrap_columns: set[int] | None = None,
) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = title[:31]
    sheet.sheet_view.showGridLines = False

    for column, header in enumerate(headers, start=1):
        cell = sheet.cell(1, column, header)
        cell.font = Font(name="Aptos", size=10, bold=True, color="FFFFFF")
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = Border(left=GRID, right=GRID, top=GRID, bottom=GRID)
    sheet.row_dimensions[1].height = 32

    row_count = 0
    for row_count, values in enumerate(rows, start=1):
        excel_row = row_count + 1
        for column, value in enumerate(values, start=1):
            if isinstance(value, Decimal):
                value = float(value)
            cell = sheet.cell(excel_row, column, value)
            cell.font = Font(name="Aptos", size=10, color="17211F")
            cell.fill = ROW_FILL if row_count % 2 else ALT_FILL
            cell.alignment = Alignment(
                horizontal="left",
                vertical="center",
                wrap_text=bool(wrap_columns and column in wrap_columns),
            )
            cell.border = Border(left=GRID, right=GRID, top=GRID, bottom=GRID)
            if date_columns and column in date_columns and value is not None:
                cell.number_format = "dd-mmm-yyyy"
            if currency_columns and column in currency_columns and value is not None:
                cell.number_format = '£#,##0.00'
        if wrap_columns:
            sheet.row_dimensions[excel_row].height = 28

    last_column = get_column_letter(len(headers))
    final_row = max(1, row_count + 1)
    sheet.auto_filter.ref = f"A1:{last_column}{final_row}"
    sheet.freeze_panes = "A2"
    for index, width in enumerate(widths, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = width
    sheet.print_title_rows = "1:1"
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def _source_values(booking: Booking) -> dict[str, Any]:
    source_rows = (booking.raw_data or {}).get("source_rows") or []
    if not source_rows:
        return {}
    return source_rows[-1].get("values") or {}


def build_bookings_export(bookings: list[Booking]) -> bytes:
    headers = [
        "Booking Reference", "Date", "Source", "Travel date", "Agent", "Team",
        "Selling cost", "Profit", "Type", "Booking matches", "Dates Check",
        "Products checked", "ABTA checked", "Special Requests",
        "Special request status Y/N", "For SF/FD/CAX", "Deposit or payment collected",
        "Product status", "Pending products", "E-tickets",
        "All attachments included (PDFs, confirmations, etc.)",
        "Follow-up call or email made post-travel",
        "Passenger confirmed everything went well",
        "Complaints/issues reported by client", "Booking marked as complete/closed",
    ]

    def row(booking: Booking) -> list[Any]:
        raw = _source_values(booking)
        return [
            booking.booking_reference, booking.booking_date, booking.source, booking.travel_date,
            booking.agent, booking.team, booking.selling_cost, booking.profit,
            booking.booking_type, booking.booking_status, raw.get("dates_check"),
            raw.get("products_checked"), raw.get("abta_checked"), booking.special_requests,
            raw.get("special_request_status"), raw.get("booking_action"), booking.payment_status,
            booking.product_status, booking.pending_products, raw.get("e_tickets"),
            booking.attachments_status, raw.get("follow_up_status"),
            raw.get("passenger_confirmation"), raw.get("complaints"),
            raw.get("completion_status"),
        ]

    return _build_workbook(
        "Bookings",
        headers,
        (row(booking) for booking in bookings),
        [20, 14, 15, 14, 18, 18, 15, 13, 16, 18, 15, 17, 15, 30, 23, 22, 27, 18, 28, 16, 38, 34, 34, 34, 32],
        date_columns={2, 4},
        currency_columns={7, 8},
        wrap_columns={14, 16, 19, 21, 22, 23, 24, 25},
    )


def build_errors_export(errors: list[ErrorRecord]) -> bytes:
    headers = [
        "Booking Reference", "Department", "Issue found date", "Issue Found",
        "Reported to", "Remark", "Status", "Action Taken", "Responsible Agent",
        "Handled Agent",
    ]
    rows = (
        [
            error.booking_reference, error.department, error.issue_date, error.issue_text,
            error.reported_to, error.remarks, error.raw_status or error.status,
            error.action_taken, error.responsible_agent, error.handled_agent,
        ]
        for error in errors
    )
    return _build_workbook(
        "Errors",
        headers,
        rows,
        [20, 18, 17, 62, 18, 38, 16, 38, 20, 20],
        date_columns={3},
        wrap_columns={4, 6, 8},
    )
