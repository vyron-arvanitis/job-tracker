from sqlalchemy import select
from email.utils import parseaddr
from job_tracker.classifier.base import EmailInput
from job_tracker.database.models import Application, Email
from job_tracker.matching.application_matcher import find_application, normalize
from job_tracker.services.status_resolver import next_action_for_status, resolve_status
from job_tracker.services.filters import is_excluded_message

def ingest_messages(session, messages, classifier, no_response_days=14, now=None, excluded_terms=()):
    # Keep newly-created applications visible within this batch as well as in
    # the database. This prevents two messages in the same sync from racing
    # toward the same unique company/role key.
    pending_apps = {}
    for message in messages:
        if is_excluded_message(message, excluded_terms):
            continue
        if session.scalar(select(Email).where(Email.gmail_message_id == message.message_id)): continue
        result = classifier.classify(EmailInput(message.sender, message.subject, message.body_text, message.sent_at))
        if not result.is_job_related: continue
        company = result.company or "Unknown company"
        position = result.position or "Unknown position"
        app_key = (normalize(company), normalize(position))
        app = pending_apps.get(app_key) or find_application(session, result.company, result.position, message.thread_id)
        if app is None:
            app = Application(company=company, position=position, company_key=normalize(company), position_key=normalize(position), source=message.sender)
            session.add(app); session.flush()
            pending_apps[app_key] = app
        session.add(Email(gmail_message_id=message.message_id, gmail_thread_id=message.thread_id, application_id=app.id, sender=message.sender, recipients=message.recipients, subject=message.subject, sent_at=message.sent_at, body_text=message.body_text, classification=result.event_type, company=result.company, position=result.position, is_sent=message.is_sent)); session.flush()
        if not message.is_sent:
            contact = parseaddr(message.sender)[1]
            if contact:
                app.contact_email = contact
        all_events = [(e.sent_at, e.classification) for e in app.emails if e.classification]
        app.applied_date = min((e.sent_at for e in app.emails if e.classification == "application_received"), default=app.applied_date)
        app.last_contact_date = max(e.sent_at for e in app.emails)
        if not app.status_override:
            resolved = resolve_status(all_events, app.applied_date, now, no_response_days)
            app.status = resolved.value
            app.next_action = result.next_action or next_action_for_status(resolved)
    session.commit()


def refresh_statuses(session, no_response_days=14, now=None):
    """Recompute derived statuses even when a sync finds no new messages."""
    from sqlalchemy import select
    from job_tracker.database.models import Application
    for app in session.scalars(select(Application)):
        if app.status_override:
            app.status = app.status_override
            app.next_action = None
            continue
        events = [(email.sent_at, email.classification) for email in app.emails if email.classification]
        status = resolve_status(events, app.applied_date, now, no_response_days)
        app.status = status.value
        app.next_action = next_action_for_status(status)
    session.commit()
