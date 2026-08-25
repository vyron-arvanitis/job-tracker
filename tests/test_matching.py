from datetime import datetime, timezone
from job_tracker.database.models import Application, Email
from job_tracker.database.session import make_session_factory
from job_tracker.gmail.client import GmailMessage
from job_tracker.classifier.rules import RuleBasedClassifier
from job_tracker.services.ingestion import ingest_messages

def msg(mid, thread, subject):
    return GmailMessage(mid, thread, "recruiter@unit8.com", "me@example.com", subject, datetime.now(timezone.utc), subject + " for the Palantir Foundry Engineer position")

def test_same_thread_and_role_become_one_application():
    factory = make_session_factory("sqlite:///:memory:")
    with factory() as session:
        ingest_messages(session, [msg("1", "t", "Thank you for applying"), msg("2", "t", "Technical interview")], RuleBasedClassifier())
        apps = session.query(Application).all()
        assert len(apps) == 1
        assert apps[0].status == "technical_interview"
        ingest_messages(session, [msg("1", "t", "Thank you for applying")], RuleBasedClassifier())
        assert len(session.query(Email).all()) == 2

def test_same_company_different_roles_remain_separate():
    factory = make_session_factory("sqlite:///:memory:")
    with factory() as session:
        first = GmailMessage("1", "t1", "recruiter@pwc.com", "me@example.com", "Thank you for applying", datetime.now(timezone.utc), "Thank you for applying for the Audit position")
        second = GmailMessage("2", "t2", "recruiter@pwc.com", "me@example.com", "Thank you for applying", datetime.now(timezone.utc), "Thank you for applying for the Data & Analytics position")
        ingest_messages(session, [first, second], RuleBasedClassifier())
        assert len(session.query(Application).all()) == 2


def test_different_roles_in_one_thread_remain_separate():
    factory = make_session_factory("sqlite:///:memory:")
    first = GmailMessage(
        "1",
        "same-thread",
        "recruiting@mckinsey.com",
        "me@example.com",
        "Your McKinsey application",
        datetime.now(timezone.utc),
        "Dear Vyron, Thank you for your interest in the Associate role at McKinsey.",
    )
    second = GmailMessage(
        "2",
        "same-thread",
        "recruiting@mckinsey.com",
        "me@example.com",
        "Your McKinsey application",
        datetime.now(timezone.utc),
        "Dear Vyron, Thank you for your interest in the Junior Associate role at McKinsey.",
    )

    with factory() as session:
        ingest_messages(session, [first, second], RuleBasedClassifier())
        assert sorted(app.position for app in session.query(Application).all()) == [
            "Associate",
            "Junior Associate",
        ]


def test_existing_unknown_position_is_reused_on_later_sync():
    factory = make_session_factory("sqlite:///:memory:")
    first = GmailMessage("1", "t1", "emails@efinancialcareers.com", "me@example.com", "Your application", datetime.now(timezone.utc), "Your application has been received")
    second = GmailMessage("2", "t2", "emails@efinancialcareers.com", "me@example.com", "Application update", datetime.now(timezone.utc), "We have an update on your application")
    with factory() as session:
        ingest_messages(session, [first], RuleBasedClassifier())
        ingest_messages(session, [second], RuleBasedClassifier())
        assert len(session.query(Application).all()) == 1
        assert len(session.query(Email).all()) == 2
