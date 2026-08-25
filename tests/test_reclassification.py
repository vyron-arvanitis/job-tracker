from datetime import datetime, timezone

from job_tracker.classifier.base import ClassificationResult, EmailInput
from job_tracker.classifier.rules import RuleBasedClassifier
from job_tracker.database.models import Application, Email
from job_tracker.database.session import make_session_factory
from job_tracker.gmail.client import GmailMessage
from job_tracker.services.ingestion import ingest_messages, reclassify_emails


def test_reclassify_updates_existing_email_and_application_status():
    factory = make_session_factory("sqlite:///:memory:")
    message = GmailMessage(
        "1",
        "thread-1",
        "recruiter@unit8.com",
        "me@example.com",
        "Application update",
        datetime(2026, 8, 1, tzinfo=timezone.utc),
        "Thank you for applying for the Software Engineer position.",
    )

    class RejectionClassifier:
        def classify(self, email: EmailInput) -> ClassificationResult:
            return ClassificationResult(
                True,
                "Unit8",
                "Software Engineer",
                "rejection",
                1.0,
            )

    with factory() as session:
        ingest_messages(session, [message], RuleBasedClassifier())
        email = session.query(Email).one()
        assert email.classification == "application_received"

        processed, changed = reclassify_emails(session, RejectionClassifier())

        assert (processed, changed) == (1, 1)
        assert email.classification == "rejection"
        assert session.query(Application).one().status == "rejected"


def test_reclassify_is_idempotent_when_rules_have_not_changed():
    factory = make_session_factory("sqlite:///:memory:")
    message = GmailMessage(
        "1",
        "thread-1",
        "recruiter@unit8.com",
        "me@example.com",
        "Technical interview",
        datetime.now(timezone.utc),
        "We would like to invite you to a technical interview for the Engineer position.",
    )

    with factory() as session:
        ingest_messages(session, [message], RuleBasedClassifier())

        assert reclassify_emails(session, RuleBasedClassifier()) == (1, 0)


def test_reclassify_detaches_stored_noise_from_job_pipeline():
    factory = make_session_factory("sqlite:///:memory:")
    message = GmailMessage(
        "1",
        "thread-1",
        "recruiter@unit8.com",
        "me@example.com",
        "Application update",
        datetime.now(timezone.utc),
        "Thank you for applying for the Software Engineer position.",
    )

    class NoiseClassifier:
        def classify(self, email: EmailInput) -> ClassificationResult:
            return ClassificationResult(False, None, None, "unknown", 0.99)

    with factory() as session:
        ingest_messages(session, [message], RuleBasedClassifier())
        processed, changed = reclassify_emails(session, NoiseClassifier())

        assert (processed, changed) == (1, 1)
        email = session.query(Email).one()
        assert email.classification is None
        assert email.application_id is None
        assert session.query(Application).count() == 0


def test_reclassify_splits_existing_same_thread_roles():
    factory = make_session_factory("sqlite:///:memory:")
    messages = [
        GmailMessage(
            "1",
            "same-thread",
            "recruiting@mckinsey.com",
            "me@example.com",
            "Your McKinsey application",
            datetime(2026, 8, 1, tzinfo=timezone.utc),
            "Dear Vyron, Thank you for your interest in the Associate role at McKinsey.",
        ),
        GmailMessage(
            "2",
            "same-thread",
            "recruiting@mckinsey.com",
            "me@example.com",
            "Your McKinsey application",
            datetime(2026, 8, 2, tzinfo=timezone.utc),
            "Dear Vyron, Thank you for your interest in the Junior Associate role at McKinsey.",
        ),
    ]

    class LegacyClassifier:
        def classify(self, email: EmailInput) -> ClassificationResult:
            return ClassificationResult(
                True,
                "Mckinsey",
                "at McKinsey",
                "application_received",
                1.0,
            )

    with factory() as session:
        ingest_messages(session, messages, LegacyClassifier())
        assert session.query(Application).count() == 1

        reclassify_emails(session, RuleBasedClassifier())

        assert sorted(app.position for app in session.query(Application).all()) == [
            "Associate",
            "Junior Associate",
        ]
