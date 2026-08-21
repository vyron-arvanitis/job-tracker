from __future__ import annotations

from datetime import datetime, timedelta, timezone
from job_tracker.database.models import ApplicationStatus

EVENT_STATUS = {"application_received": ApplicationStatus.APPLIED, "recruiter_contact": ApplicationStatus.APPLIED, "hr_interview": ApplicationStatus.HR_INTERVIEW, "technical_interview": ApplicationStatus.TECHNICAL_INTERVIEW, "assessment": ApplicationStatus.ASSESSMENT, "final_interview": ApplicationStatus.FINAL_INTERVIEW, "rejection": ApplicationStatus.REJECTED, "offer": ApplicationStatus.OFFER, "withdrawal": ApplicationStatus.WITHDRAWN}

def resolve_status(events: list[tuple[object, str]], applied_date=None, now=None, no_response_days=14) -> ApplicationStatus:
    status = ApplicationStatus.UNKNOWN
    for _, event in sorted(events, key=lambda item: _utc(item[0]) if isinstance(item[0], datetime) else item[0]): status = EVENT_STATUS.get(event, status)
    now = _utc(now or datetime.now(timezone.utc))
    applied_date = _utc(applied_date) if applied_date else None
    if status == ApplicationStatus.APPLIED and applied_date and now - applied_date > timedelta(days=no_response_days): status = ApplicationStatus.NO_RESPONSE
    return status


def _utc(value: datetime) -> datetime:
    """Treat SQLite's naive timestamps as UTC and normalize aware values."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def next_action_for_status(status: ApplicationStatus) -> str | None:
    return {
        ApplicationStatus.NO_RESPONSE: "Consider follow-up",
        ApplicationStatus.HR_INTERVIEW: "Prepare for HR interview",
        ApplicationStatus.TECHNICAL_INTERVIEW: "Prepare for technical interview",
        ApplicationStatus.ASSESSMENT: "Complete the assessment",
        ApplicationStatus.FINAL_INTERVIEW: "Prepare for final interview",
        ApplicationStatus.REJECTED: None,
        ApplicationStatus.OFFER: "Review offer",
    }.get(status)
