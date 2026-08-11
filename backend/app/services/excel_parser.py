from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Any

import pandas as pd

from app.services.normalization import (
    categorize_issue,
    clean_text,
    issue_hash,
    json_safe,
    normalize_agent,
    normalize_booking_reference,
    normalize_error_status,
    normalize_header,
    normalize_issue,
    parse_excel_date,
    parse_money,
)


@dataclass
class ParsedWorkbook:
    bookings: list[dict[str, Any]]
    errors: list[dict[str, Any]]
    summary: dict[str, Any]


def _normalized_frame(frame: pd.DataFrame) -> pd.DataFrame:
    columns: list[str] = []
    used: dict[str, int] = {}
    for source in frame.columns:
        name = normalize_header(source)
        used[name] = used.get(name, 0) + 1
        columns.append(name if used[name] == 1 else f"{name}_{used[name]}")
    result = frame.copy()
    result.columns = columns
    return result


def detect_sheet_type(frame: pd.DataFrame) -> str | None:
    names = {normalize_header(col) for col in frame.columns}
    if {"booking_reference", "issue_text"}.issubset(names):
        return "errors"
    if "booking_reference" in names and len({"agent", "team", "travel_date", "selling_cost"} & names) >= 2:
        return "bookings"
    return None


def inspect_workbook(content: bytes) -> dict[str, Any]:
    xls = pd.ExcelFile(BytesIO(content), engine="openpyxl")
    sheets = []
    for name in xls.sheet_names:
        frame = pd.read_excel(xls, sheet_name=name)
        sheets.append({
            "name": name,
            "rows": int(len(frame)),
            "columns": [str(col) for col in frame.columns],
            "detected_type": detect_sheet_type(frame),
        })
    return {"sheets": sheets}


def parse_workbook(content: bytes) -> ParsedWorkbook:
    xls = pd.ExcelFile(BytesIO(content), engine="openpyxl")
    booking_frames: list[tuple[str, pd.DataFrame]] = []
    error_frames: list[tuple[str, pd.DataFrame]] = []
    sheet_summary: list[dict[str, Any]] = []
    for sheet_name in xls.sheet_names:
        source = pd.read_excel(xls, sheet_name=sheet_name)
        kind = detect_sheet_type(source)
        sheet_summary.append({"name": sheet_name, "rows": int(len(source)), "columns": len(source.columns), "detected_type": kind})
        if kind == "bookings":
            booking_frames.append((sheet_name, _normalized_frame(source)))
        elif kind == "errors":
            error_frames.append((sheet_name, _normalized_frame(source)))
    if not booking_frames:
        raise ValueError("No booking sheet could be detected. Include booking reference plus agent/team/travel columns.")
    if not error_frames:
        raise ValueError("No error sheet could be detected. Include booking reference and issue text columns.")

    bookings_by_ref: dict[str, dict[str, Any]] = {}
    missing_refs = 0
    duplicate_reference_rows = 0
    for sheet_name, frame in booking_frames:
        for row_number, raw_row in enumerate(frame.to_dict("records"), start=2):
            raw = {key: json_safe(value) for key, value in raw_row.items()}
            ref = normalize_booking_reference(raw_row.get("booking_reference"))
            if not ref:
                missing_refs += 1
                continue
            record = {
                "booking_reference": ref,
                "booking_date": parse_excel_date(raw_row.get("booking_date")),
                "travel_date": parse_excel_date(raw_row.get("travel_date")),
                "agent": normalize_agent(raw_row.get("agent")),
                "team": clean_text(raw_row.get("team")),
                "source": clean_text(raw_row.get("source")),
                "selling_cost": parse_money(raw_row.get("selling_cost")),
                "profit": parse_money(raw_row.get("profit")),
                "booking_type": clean_text(raw_row.get("booking_type")),
                "booking_status": clean_text(raw_row.get("booking_status")),
                "payment_status": clean_text(raw_row.get("payment_status")),
                "product_status": clean_text(raw_row.get("product_status")),
                "pending_products": clean_text(raw_row.get("pending_products")),
                "special_requests": clean_text(raw_row.get("special_requests")),
                "attachments_status": clean_text(raw_row.get("attachments_status")),
                "quality_checks": {
                    "booking_details": clean_text(raw_row.get("booking_status")),
                    "dates": clean_text(raw_row.get("dates_check")),
                    "products": clean_text(raw_row.get("products_checked")),
                    "payment": clean_text(raw_row.get("payment_status")),
                    "attachments": clean_text(raw_row.get("attachments_status")),
                },
                "raw_data": {"source_rows": [{"sheet": sheet_name, "row": row_number, "values": raw}]},
            }
            existing = bookings_by_ref.get(ref)
            if existing:
                duplicate_reference_rows += 1
                source_rows = existing["raw_data"]["source_rows"] + record["raw_data"]["source_rows"]
                if (record["booking_date"] or pd.Timestamp.min.date()) >= (existing["booking_date"] or pd.Timestamp.min.date()):
                    record["raw_data"] = {"source_rows": source_rows}
                    bookings_by_ref[ref] = record
                else:
                    existing["raw_data"]["source_rows"] = source_rows
            else:
                bookings_by_ref[ref] = record

    errors: list[dict[str, Any]] = []
    exact_error_keys: set[tuple[Any, ...]] = set()
    duplicate_errors = 0
    for sheet_name, frame in error_frames:
        for row_number, raw_row in enumerate(frame.to_dict("records"), start=2):
            raw = {key: json_safe(value) for key, value in raw_row.items()}
            ref = normalize_booking_reference(raw_row.get("booking_reference"))
            issue = clean_text(raw_row.get("issue_text"))
            if not ref or not issue:
                continue
            normalized = normalize_issue(issue)
            status = normalize_error_status(raw_row.get("error_status"))
            responsible = normalize_agent(raw_row.get("responsible_agent"))
            handled = normalize_agent(raw_row.get("handled_agent"))
            key = (ref, normalized, status, responsible, handled, parse_excel_date(raw_row.get("issue_date")))
            if key in exact_error_keys:
                duplicate_errors += 1
                continue
            exact_error_keys.add(key)
            category, severity = categorize_issue(issue)
            errors.append({
                "booking_reference": ref,
                "department": clean_text(raw_row.get("department")),
                "issue_date": parse_excel_date(raw_row.get("issue_date")),
                "issue_text": issue,
                "normalized_issue": normalized,
                "issue_hash": issue_hash(issue),
                "status": status,
                "raw_status": clean_text(raw_row.get("error_status")),
                "responsible_agent": responsible,
                "handled_agent": handled,
                "reported_to": clean_text(raw_row.get("reported_to")),
                "remarks": clean_text(raw_row.get("remarks")),
                "action_taken": clean_text(raw_row.get("action_taken")),
                "category": category,
                "severity": severity,
                "raw_data": {"sheet": sheet_name, "row": row_number, "values": raw},
            })

    booking_refs = set(bookings_by_ref)
    unmatched = [error for error in errors if error["booking_reference"] not in booking_refs]
    summary = {
        "sheets": sheet_summary,
        "booking_rows_detected": sum(item[1].shape[0] for item in booking_frames),
        "bookings_imported": len(bookings_by_ref),
        "error_rows_detected": sum(item[1].shape[0] for item in error_frames),
        "errors_imported": len(errors),
        "missing_booking_references": missing_refs,
        "duplicate_booking_references_merged": duplicate_reference_rows,
        "duplicate_errors_skipped": duplicate_errors,
        "matched_error_rows": len(errors) - len(unmatched),
        "unmatched_error_rows": len(unmatched),
        "unmatched_error_references": len({error["booking_reference"] for error in unmatched}),
    }
    return ParsedWorkbook(bookings=list(bookings_by_ref.values()), errors=errors, summary=summary)

