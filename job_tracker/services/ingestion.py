from datetime import datetime, timezone
from sqlalchemy import select
from email.utils import parseaddr
from job_tracker.classifier.base import EmailInput
from job_tracker.database.models import Application, Email
from job_tracker.matching.application_matcher import find_application, normalize
from job_tracker.services.status_resolver import next_action_for_status, resolve_status
from job_tracker.services.filters import is_excluded_message


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)

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
        # Use the same fallback values for matching that are used when the
        # application is created. Otherwise a classifier result with a missing
        # position (or company) cannot find an existing "Unknown ..." row and
        # the insert below violates uq_application_role.
        app = pending_apps.get(app_key) or find_application(session, company, position, message.thread_id)
        if app is None:
            app = Application(company=company, position=position, company_key=normalize(company), position_key=normalize(position), source=message.sender)
            session.add(app); session.flush()
            pending_apps[app_key] = app
        email = Email(gmail_message_id=message.message_id, gmail_thread_id=message.thread_id, application=app, sender=message.sender, recipients=message.recipients, subject=message.subject, sent_at=message.sent_at, body_text=message.body_text, classification=result.event_type, company=result.company, position=result.position, is_sent=message.is_sent)
        session.add(email); session.flush()
        if not message.is_sent:
            contact = parseaddr(message.sender)[1]
            if contact:
                app.contact_email = contact
        all_events = [(e.sent_at, e.classification) for e in app.emails if e.classification]
        application_dates = [e.sent_at for e in app.emails if e.classification == "application_received"]
        app.applied_date = min(application_dates, key=_utc, default=app.applied_date)
        app.last_contact_date = max((e.sent_at for e in app.emails), key=_utc)
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


def reclassify_emails(session, classifier, no_response_days=14, now=None) -> tuple[int, int]:
    """Re-run classification for all emails already stored locally.

    Gmail is not contacted and message IDs are not changed. Application
    associations for genuine job emails remain stable. Messages that the
    classifier identifies as non-job mail are detached from applications, and
    applications with no genuine job emails left are removed. The application
    fields derived from the remaining classifications are then rebuilt.

    Returns ``(processed, changed)``.
    """
    emails = list(session.scalars(select(Email).order_by(Email.id)))
    attached_application_ids = {
        email.application_id for email in emails if email.application_id is not None
    }
    changed = 0
    for email in emails:
        result = classifier.classify(
            EmailInput(
                email.sender,
                email.subject,
                email.body_text or "",
                email.sent_at,
            )
        )
        old_values = (
            email.classification,
            email.company,
            email.position,
            email.application_id,
        )
        if result.is_job_related:
            new_values = (
                result.event_type if result.event_type else None,
                result.company,
                result.position,
                email.application_id,
            )
        else:
            # Keep the raw email row for local audit/reclassification, but do
            # not leave newsletters, university notices, or account messages
            # in the job pipeline.
            new_values = (None, None, None, None)
            email.application = None
        if old_values != new_values:
            changed += 1
        email.classification, email.company, email.position = new_values[:3]

    # Remove rows created by the old broad classifier when every attached
    # message has now been identified as non-job mail.
    applications = list(session.scalars(select(Application)))
    for app in applications:
        if app.id in attached_application_ids and not app.emails:
            session.delete(app)

    for app in applications:
        if app in session.deleted:
            continue
        application_dates = [
            email.sent_at
            for email in app.emails
            if email.classification == "application_received"
        ]
        app.applied_date = min(application_dates, key=_utc, default=None)
        app.last_contact_date = max(
            (email.sent_at for email in app.emails),
            key=_utc,
            default=None,
        )

    session.flush()
    refresh_statuses(session, no_response_days, now)
    return len(emails), changed
