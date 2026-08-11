from __future__ import annotations

import hashlib
import math
import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd


HEADER_ALIASES: dict[str, set[str]] = {
    "booking_reference": {"", "booking ref", "booking reference", "booking_reference", "reference", "booking id"},
    "booking_date": {"date", "booking date", "created date"},
    "travel_date": {"travel date", "departure date"},
    "agent": {"agent", "booking agent", "sales agent"},
    "team": {"team", "sales team"},
    "source": {"source", "booking source"},
    "selling_cost": {"selling cost", "selling value", "booking value", "sale value"},
    "profit": {"profit", "margin"},
    "booking_type": {"type", "booking type"},
    "booking_status": {"booking status", "booking matches", "status match"},
    "dates_check": {"dates check", "date check"},
    "products_checked": {"products checked", "product check"},
    "abta_checked": {"abta checked", "abta check"},
    "special_requests": {"special requests", "special request"},
    "special_request_status": {"special request status y n", "special request status"},
    "booking_action": {"for sf fd cax", "booking action"},
    "payment_status": {"deposit or payment collected", "payment status", "deposit status"},
    "product_status": {"product status", "products status"},
    "pending_products": {"pending products", "pending product"},
    "e_tickets": {"e tickets", "etickets", "e-tickets"},
    "attachments_status": {"all attachments included pdfs confirmations etc", "attachments", "attachment status"},
    "follow_up_status": {"follow up call or email made post travel", "post travel follow up"},
    "passenger_confirmation": {"passenger confirmed everything went well", "passenger confirmation"},
    "complaints": {"complaints issues reported by client", "complaints", "client issues"},
    "completion_status": {"booking marked as complete closed", "completion status"},
    "department": {"department"},
    "issue_date": {"issue found date", "issue date", "error date"},
    "issue_text": {"issue found", "issue", "error", "error description"},
    "reported_to": {"reported to"},
    "remarks": {"remark", "remarks"},
    "error_status": {"status", "error status", "issue status"},
    "action_taken": {"action taken", "resolution action"},
    "responsible_agent": {"responsible agent", "agent responsible"},
    "handled_agent": {"handled agent", "handled by", "handling agent"},
}


def normalize_header(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        cleaned = ""
    else:
        cleaned = str(value).strip().casefold()
        cleaned = re.sub(r"[^a-z0-9]+", " ", cleaned).strip()
    if cleaned.startswith("unnamed"):
        return "booking_reference"
    for canonical, aliases in HEADER_ALIASES.items():
        if cleaned in aliases:
            return canonical
    return cleaned.replace(" ", "_") or "booking_reference"


def clean_text(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text or None


def normalize_booking_reference(value: Any) -> str | None:
    text = clean_text(value)
    if text is None:
        return None
    text = re.sub(r"\.0$", "", text).upper().replace(" ", "")
    return text or None


def normalize_agent(value: Any) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    return " ".join(part.capitalize() for part in text.split())


def normalize_error_status(value: Any) -> str:
    text = (clean_text(value) or "").casefold()
    compact = re.sub(r"[^a-z]", "", text)
    if compact in {"sorted", "sorrted", "resolved", "closed", "complete", "completed"}:
        return "resolved"
    if "pending" in compact or "progress" in compact:
        return "pending"
    return "open"


def parse_excel_date(value: Any) -> date | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)) and 1 <= float(value) <= 100000:
        return (datetime(1899, 12, 30) + timedelta(days=float(value))).date()
    text = clean_text(value)
    if text and re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", text):
        parsed_iso = pd.to_datetime(text, format="%Y-%m-%d", errors="coerce")
        return None if pd.isna(parsed_iso) else parsed_iso.date()
    parsed = pd.to_datetime(value, errors="coerce", dayfirst=True)
    return None if pd.isna(parsed) else parsed.date()


def parse_money(value: Any) -> Decimal | None:
    if value is None or pd.isna(value):
        return None
    text = re.sub(r"[^0-9.\-]", "", str(value).replace(",", ""))
    if not text:
        return None
    try:
        return Decimal(text).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def normalize_issue(value: Any) -> str:
    return (clean_text(value) or "").casefold()


def issue_hash(value: str) -> str:
    return hashlib.sha256(normalize_issue(value).encode("utf-8")).hexdigest()


CATEGORY_RULES = [
    ("Passenger Details", r"pax name|passenger name|date of birth|dob|title differs|name entered|passport"),
    ("Flight / PNR", r"\bpnr\b|flight|seat|airline|ticket|baggage|cabin|itinerary"),
    ("Hotel", r"hotel|room|bed|check.?in|check.?out|accommodation|resort"),
    ("Documentation", r"voucher|confirmation|attach|document|pdf|proof|quote ref|reference"),
    ("Payment", r"payment|balance|paid|refund|card"),
    ("Deposit", r"deposit|instalment|installment"),
    ("Pricing", r"price|fare|cost|rate|profit|cheaper|difference"),
    ("Product Availability", r"not available|allocation|allocate|pending product|sold out"),
    ("Special Request", r"special req|birthday|anniversary|meal|wheelchair|assistance"),
    ("Transfer", r"transfer|pick.?up|drop.?off|taxi"),
    ("Insurance", r"insurance"),
    ("Communication", r"email|mail|contact|call|reply|advise agent|inform"),
    ("Booking Process", r"booking|booked|admin|summary table|need to proceed|cancel"),
]


def categorize_issue(text: str) -> tuple[str, str]:
    normalized = normalize_issue(text)
    category = next((name for name, pattern in CATEGORY_RULES if re.search(pattern, normalized)), "Other")
    if re.search(r"name.*wrong|wrong.*name|cancel|not available|missing flight|refund|duplicate payment", normalized):
        severity = "High"
    elif re.search(r"missing|differ|wrong|pending|not attached|not added|incorrect", normalized):
        severity = "Medium"
    else:
        severity = "Low"
    return category, severity


def json_safe(value: Any) -> Any:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "item"):
        return value.item()
    return value
