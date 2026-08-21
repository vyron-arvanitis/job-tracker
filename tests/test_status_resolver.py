from datetime import datetime, timedelta, timezone
from job_tracker.services.status_resolver import resolve_status

def test_transitions_are_chronological():
    base = datetime(2026, 7, 1, tzinfo=timezone.utc)
    assert resolve_status([(base, "application_received"), (base + timedelta(days=2), "hr_interview")]) == "hr_interview"
    assert resolve_status([(base, "application_received"), (base + timedelta(days=2), "hr_interview"), (base + timedelta(days=3), "rejection")]) == "rejected"
    assert resolve_status([(base, "application_received"), (base + timedelta(days=2), "hr_interview"), (base + timedelta(days=3), "offer")]) == "offer"

def test_no_response_is_derived():
    base = datetime(2026, 7, 1, tzinfo=timezone.utc)
    assert resolve_status([(base, "application_received")], base, base + timedelta(days=15)) == "no_response"

