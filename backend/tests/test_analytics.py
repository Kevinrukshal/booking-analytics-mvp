from datetime import date
from decimal import Decimal

from app.db.models import Booking, ErrorRecord
from app.services.analytics import agent_metrics


def booking(reference: str, agent: str) -> Booking:
    return Booking(upload_id=1, booking_reference=reference, booking_date=date(2026, 8, 1), agent=agent, team="A", profit=Decimal("100"), quality_checks={}, raw_data={})


def error(reference: str, status: str = "open") -> ErrorRecord:
    return ErrorRecord(upload_id=1, booking_reference=reference, issue_text="Issue", normalized_issue="issue", issue_hash=reference, status=status, category="Other", severity="Low", raw_data={})


def test_agent_error_rate_uses_unique_error_bookings(monkeypatch):
    from app.services import analytics
    monkeypatch.setattr(analytics.settings, "min_agent_bookings", 1)
    bookings = [booking("1", "Alex"), booking("2", "Alex")]
    errors = [error("1"), error("1"), error("2", "resolved")]
    metric = agent_metrics(bookings, errors)[0]
    assert metric["errorBookings"] == 2
    assert metric["errorRate"] == 1.0
    assert metric["openErrors"] == 2
