from types import SimpleNamespace

from job_tracker.reporting import cumulative_applied_count, status_label


def test_applied_count_includes_applications_at_every_stage():
    applications = [
        SimpleNamespace(status="applied"),
        SimpleNamespace(status="no_response"),
        SimpleNamespace(status="hr_interview"),
        SimpleNamespace(status="rejected"),
    ]

    assert cumulative_applied_count(applications) == 4


def test_current_applied_stage_is_displayed_as_awaiting_response():
    assert status_label("applied") == "Awaiting response"
    assert status_label("no_response") == "No Response"
