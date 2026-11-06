from datetime import date
from decimal import Decimal

import pytest

from app.services.normalization import (
    categorize_issue,
    normalize_agent,
    normalize_booking_reference,
    normalize_error_status,
    normalize_header,
    parse_excel_date,
    parse_money,
)


@pytest.mark.parametrize("source", ["Booking Ref", "Booking Reference", "booking reference", " "])
def test_header_normalization(source):
    assert normalize_header(source) == "booking_reference"


def test_reference_and_agent_normalization():
    assert normalize_booking_reference(1000001.0) == "1000001"
    assert normalize_booking_reference(" e 10001 ") == "E10001"
    assert normalize_agent("  dEMO aGENT  ") == "Demo Agent"


def test_date_and_money_parsing():
    assert parse_excel_date(46235) == date(2026, 8, 1)
    assert parse_excel_date("11/08/2026") == date(2026, 8, 11)
    assert parse_money("£1,234.50") == Decimal("1234.50")


def test_status_and_category_normalization():
    assert normalize_error_status("Sorrted") == "resolved"
    assert normalize_error_status("Not actoned") == "open"
    category, severity = categorize_issue("Pax name entered wrong in PNR")
    assert category == "Passenger Details"
    assert severity == "High"
