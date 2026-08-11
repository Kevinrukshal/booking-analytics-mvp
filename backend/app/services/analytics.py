from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from typing import Any
from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Booking, ErrorRecord, Upload


def latest_upload(db: Session) -> Upload | None:
    return db.scalar(select(Upload).where(Upload.status == "completed").order_by(Upload.created_at.desc(), Upload.id.desc()).limit(1))


def money(value: Decimal | None) -> float:
    return float(value or 0)


def booking_dict(booking: Booking, counts: dict[str, dict[str, int]] | None = None) -> dict[str, Any]:
    error_counts = (counts or {}).get(booking.booking_reference, {"errors": 0, "open": 0})
    return {
        "id": booking.id,
        "bookingReference": booking.booking_reference,
        "bookingDate": booking.booking_date,
        "travelDate": booking.travel_date,
        "agent": booking.agent,
        "team": booking.team,
        "source": booking.source,
        "sellingCost": money(booking.selling_cost),
        "profit": money(booking.profit),
        "bookingType": booking.booking_type,
        "bookingStatus": booking.booking_status,
        "paymentStatus": booking.payment_status,
        "productStatus": booking.product_status,
        "pendingProducts": booking.pending_products,
        "specialRequests": booking.special_requests,
        "attachmentsStatus": booking.attachments_status,
        "qualityChecks": booking.quality_checks,
        "errorCount": error_counts["errors"],
        "openErrorCount": error_counts["open"],
    }


def error_dict(error: ErrorRecord, matched: bool | None = None) -> dict[str, Any]:
    return {
        "id": error.id,
        "bookingReference": error.booking_reference,
        "department": error.department,
        "issueDate": error.issue_date,
        "issueText": error.issue_text,
        "status": error.status,
        "rawStatus": error.raw_status,
        "responsibleAgent": error.responsible_agent,
        "handledAgent": error.handled_agent,
        "reportedTo": error.reported_to,
        "remarks": error.remarks,
        "actionTaken": error.action_taken,
        "category": error.ai_category or error.category,
        "severity": error.ai_severity or error.severity,
        "aiSummary": error.ai_summary,
        "aiRecommendedAction": error.ai_recommended_action,
        "matched": matched,
    }


def error_counts(errors: list[ErrorRecord]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = defaultdict(lambda: {"errors": 0, "open": 0})
    for error in errors:
        result[error.booking_reference]["errors"] += 1
        if error.status != "resolved":
            result[error.booking_reference]["open"] += 1
    return dict(result)


def agent_metrics(bookings: list[Booking], errors: list[ErrorRecord]) -> list[dict[str, Any]]:
    refs = {booking.booking_reference for booking in bookings}
    relevant_errors = [error for error in errors if error.booking_reference in refs]
    counts = error_counts(relevant_errors)
    by_agent: dict[str, list[Booking]] = defaultdict(list)
    for booking in bookings:
        by_agent[booking.agent or "Unknown"].append(booking)
    total_error_bookings = sum(1 for booking in bookings if counts.get(booking.booking_reference, {}).get("errors", 0) > 0)
    overall_rate = total_error_bookings / len(bookings) if bookings else 0
    metrics = []
    for agent, rows in by_agent.items():
        error_bookings = sum(1 for row in rows if counts.get(row.booking_reference, {}).get("errors", 0) > 0)
        open_errors = sum(counts.get(row.booking_reference, {}).get("open", 0) for row in rows)
        rate = error_bookings / len(rows) if rows else 0
        if len(rows) < settings.min_agent_bookings:
            status = "Insufficient sample"
        elif rate < overall_rate:
            status = "Healthy"
        elif rate <= overall_rate * 1.5:
            status = "Watch"
        else:
            status = "Needs Attention"
        teams = Counter(row.team or "Unknown" for row in rows)
        metrics.append({
            "agent": agent,
            "team": teams.most_common(1)[0][0],
            "bookings": len(rows),
            "errorBookings": error_bookings,
            "errorRate": rate,
            "openErrors": open_errors,
            "profit": sum(money(row.profit) for row in rows),
            "status": status,
        })
    return sorted(metrics, key=lambda item: (-item["errorRate"], -item["bookings"], item["agent"]))


def dashboard_payload(db: Session) -> dict[str, Any] | None:
    upload = latest_upload(db)
    if not upload:
        return None
    bookings = list(db.scalars(select(Booking).where(Booking.upload_id == upload.id)))
    errors = list(db.scalars(select(ErrorRecord).where(ErrorRecord.upload_id == upload.id)))
    refs = {booking.booking_reference for booking in bookings}
    current_errors = [error for error in errors if error.booking_reference in refs]
    unmatched_errors = [error for error in errors if error.booking_reference not in refs]
    counts = error_counts(current_errors)
    bookings_with_errors = sum(1 for booking in bookings if counts.get(booking.booking_reference, {}).get("errors", 0))
    open_errors = sum(1 for error in current_errors if error.status != "resolved")
    pending = [booking for booking in bookings if booking.pending_products or (booking.product_status or "").casefold() == "pending"]
    error_rate = bookings_with_errors / len(bookings) if bookings else 0
    multiple_open = sum(1 for booking in bookings if counts.get(booking.booking_reference, {}).get("open", 0) > 1)
    agents = agent_metrics(bookings, errors)
    above_average = sum(
        1 for agent in agents
        if agent["bookings"] >= settings.min_agent_bookings and agent["errorRate"] > error_rate
    )

    attention = []
    if open_errors:
        attention.append({"label": f"{open_errors} unresolved errors on current bookings", "context": "Review open and pending records", "href": "/errors?status=open", "tone": "critical"})
    if multiple_open:
        booking_word = "booking" if multiple_open == 1 else "bookings"
        attention.append({"label": f"{multiple_open} {booking_word} has multiple open errors" if multiple_open == 1 else f"{multiple_open} bookings have multiple open errors", "context": "Prioritize repeated quality failures", "href": "/bookings?hasErrors=true", "tone": "critical"})
    if pending:
        attention.append({"label": f"{len(pending)} bookings have pending products", "context": f"£{sum(money(row.selling_cost) for row in pending):,.0f} selling value exposed", "href": "/bookings?pendingProduct=true", "tone": "warning"})
    if above_average:
        attention.append({"label": f"{above_average} agents are above the average error rate", "context": f"Minimum {settings.min_agent_bookings} bookings", "href": "/agents", "tone": "warning"})
    if unmatched_errors:
        attention.append({"label": f"{len(unmatched_errors)} historical errors do not match this booking sheet", "context": "Retained for audit and searchable in Errors", "href": "/errors?matched=false", "tone": "neutral"})

    trend_counts: Counter[date] = Counter(error.issue_date for error in current_errors if error.issue_date)
    status_counts = Counter(error.status for error in current_errors)
    category_counts = Counter((error.ai_category or error.category) for error in current_errors)
    meaningful_agents = [agent for agent in agents if agent["bookings"] >= settings.min_agent_bookings][:8]
    if not meaningful_agents:
        meaningful_agents = sorted(agents, key=lambda item: (-item["bookings"], -item["errorRate"]))[:8]

    insights = []
    eligible = [agent for agent in agents if agent["bookings"] >= settings.min_agent_bookings]
    if eligible:
        worst = max(eligible, key=lambda item: item["errorRate"])
        insights.append({"title": "Highest meaningful agent error rate", "text": f"{worst['agent']} has a {worst['errorRate']:.1%} error rate across {worst['bookings']} bookings.", "href": f"/agents/{quote(worst['agent'])}"})
    if category_counts:
        category, count = category_counts.most_common(1)[0]
        insights.append({"title": "Most common issue", "text": f"{category} represents {count / len(current_errors):.0%} of errors linked to current bookings.", "href": f"/errors?category={quote(category)}"})
    if multiple_open:
        text = "1 booking currently has more than one unresolved error." if multiple_open == 1 else f"{multiple_open} bookings currently have more than one unresolved error."
        insights.append({"title": "Repeated open issues", "text": text, "href": "/bookings?hasErrors=true"})
    if pending:
        insights.append({"title": "Pending-product exposure", "text": f"Pending products affect {len(pending)} bookings and £{sum(money(row.selling_cost) for row in pending):,.0f} in selling value.", "href": "/bookings?pendingProduct=true"})
    if current_errors:
        resolved = status_counts.get("resolved", 0)
        insights.append({"title": "Resolution rate", "text": f"{resolved / len(current_errors):.0%} of errors linked to current bookings are resolved.", "href": "/errors"})

    return {
        "upload": {"id": upload.id, "filename": upload.filename, "createdAt": upload.created_at, "summary": upload.summary},
        "kpis": {
            "totalBookings": len(bookings),
            "bookingsWithErrors": bookings_with_errors,
            "errorRate": error_rate,
            "openErrors": open_errors,
            "pendingProducts": len(pending),
            "totalProfit": sum(money(row.profit) for row in bookings),
            "totalErrors": len(errors),
            "matchedErrors": len(current_errors),
        },
        "attention": attention[:5],
        "errorTrend": [{"date": key.isoformat(), "errors": value} for key, value in sorted(trend_counts.items())],
        "statusDistribution": [{"status": key.title(), "value": value} for key, value in status_counts.items()],
        "agentPerformance": meaningful_agents,
        "errorCategories": [{"category": key, "value": value} for key, value in category_counts.most_common(8)],
        "insights": insights[:5],
    }
