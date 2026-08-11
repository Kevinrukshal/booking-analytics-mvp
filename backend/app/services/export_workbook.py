from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from io import BytesIO
from typing import Any, Iterable

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

from app.db.models import Booking, ErrorRecord


ACCENT = "0F6D59"
ACCENT_DARK = "0D5749"
ACCENT_LIGHT = "EAF6F2"
SLATE = "475569"
LIGHT_BORDER = Side(style="thin", color="DCE3E1")


def _build_workbook(
    title: str,
    scope: str,
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
    last_column = get_column_letter(len(headers))

    sheet.merge_cells(f"A1:{last_column}1")
    sheet["A1"] = f"Booking Analytics · {title} export"
    sheet["A1"].font = Font(name="Aptos Display", size=18, bold=True, color="FFFFFF")
    sheet["A1"].fill = PatternFill("solid", fgColor=ACCENT_DARK)
    sheet["A1"].alignment = Alignment(vertical="center")
    sheet.row_dimensions[1].height = 34

    exported_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    sheet.merge_cells(f"A2:{last_column}2")
    sheet["A2"] = f"{scope} · Exported {exported_at}"
    sheet["A2"].font = Font(name="Aptos", size=10, color=SLATE)
    sheet["A2"].fill = PatternFill("solid", fgColor=ACCENT_LIGHT)
    sheet["A2"].alignment = Alignment(vertical="center")
    sheet.row_dimensions[2].height = 24

    header_row = 4
    for column, header in enumerate(headers, start=1):
        cell = sheet.cell(header_row, column, header)
        cell.font = Font(name="Aptos", size=10, bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=ACCENT)
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        cell.border = Border(bottom=LIGHT_BORDER)
    sheet.row_dimensions[header_row].height = 28

    row_count = 0
    for row_count, values in enumerate(rows, start=1):
        excel_row = header_row + row_count
        for column, value in enumerate(values, start=1):
            if isinstance(value, Decimal):
                value = float(value)
            cell = sheet.cell(excel_row, column, value)
            cell.font = Font(name="Aptos", size=10, color="1F2937")
            cell.alignment = Alignment(vertical="top", wrap_text=bool(wrap_columns and column in wrap_columns))
            cell.border = Border(bottom=LIGHT_BORDER)
            if date_columns and column in date_columns and value is not None:
                cell.number_format = "yyyy-mm-dd"
            if currency_columns and column in currency_columns and value is not None:
                cell.number_format = '£#,##0.00'

    final_row = header_row + row_count
    if row_count:
        table = Table(displayName=f"{title.replace(' ', '')}ExportTable", ref=f"A{header_row}:{last_column}{final_row}")
        table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium4", showRowStripes=True, showColumnStripes=False)
        sheet.add_table(table)
    else:
        sheet.auto_filter.ref = f"A{header_row}:{last_column}{header_row}"

    sheet.freeze_panes = "A5"
    for index, width in enumerate(widths, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = width
    sheet.auto_filter.ref = f"A{header_row}:{last_column}{max(header_row, final_row)}"
    sheet.print_title_rows = f"1:{header_row}"
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0
    sheet.auto_filter.ref = f"A{header_row}:{last_column}{max(header_row, final_row)}"

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def build_bookings_export(
    bookings: list[Booking],
    counts: dict[str, dict[str, int]],
    scope: str,
) -> bytes:
    headers = [
        "Booking Reference", "Booking Date", "Travel Date", "Agent", "Team", "Source",
        "Booking Type", "Booking Status", "Payment Status", "Product Status",
        "Pending Products", "Selling Value", "Profit", "Error Count", "Open Errors",
    ]
    rows = (
        [
            booking.booking_reference, booking.booking_date, booking.travel_date, booking.agent,
            booking.team, booking.source, booking.booking_type, booking.booking_status,
            booking.payment_status, booking.product_status, booking.pending_products,
            booking.selling_cost, booking.profit,
            counts.get(booking.booking_reference, {}).get("errors", 0),
            counts.get(booking.booking_reference, {}).get("open", 0),
        ]
        for booking in bookings
    )
    return _build_workbook(
        "Bookings", scope, headers, rows,
        [20, 14, 14, 18, 16, 16, 17, 18, 18, 18, 32, 16, 14, 13, 12],
        date_columns={2, 3}, currency_columns={12, 13}, wrap_columns={11},
    )


def build_errors_export(errors: list[ErrorRecord], booking_refs: set[str], scope: str) -> bytes:
    headers = [
        "Booking Reference", "Issue Date", "Responsible Agent", "Issue", "Category",
        "Severity", "Status", "Handled By", "Department", "Action Taken", "Remarks",
        "Matches Current Booking",
    ]
    rows = (
        [
            error.booking_reference, error.issue_date, error.responsible_agent, error.issue_text,
            error.ai_category or error.category, error.ai_severity or error.severity, error.status,
            error.handled_agent, error.department, error.action_taken, error.remarks,
            "Yes" if error.booking_reference in booking_refs else "No",
        ]
        for error in errors
    )
    return _build_workbook(
        "Errors", scope, headers, rows,
        [20, 14, 20, 48, 22, 12, 14, 20, 18, 38, 38, 24], date_columns={2},
        wrap_columns={4, 10, 11},
    )
