import csv
from datetime import timezone

from sqlalchemy import func, select

from .classifier.rules import RuleBasedClassifier
from .cli_progress import progress
from .database.models import Application, Email
from .gmail.auth import authenticate
from .gmail.client import GmailClient
from .gmail.search import candidate_queries
from .reporting import cumulative_applied_count, create_status_chart, status_counts, status_label
from .services.ingestion import ingest_messages, reclassify_emails, refresh_statuses


def authenticate_gmail(settings) -> None:
    authenticate(settings.credentials_file, settings.token_file)
    print("Gmail authentication completed.")


def sync_gmail(settings, session_factory) -> None:
    with session_factory() as session:
        latest_email = session.scalar(select(func.max(Email.sent_at)))
    if latest_email and latest_email.tzinfo is None:
        latest_email = latest_email.replace(tzinfo=timezone.utc)
    client = GmailClient.from_credentials(authenticate(settings.credentials_file, settings.token_file))
    ids = set()
    queries = candidate_queries(latest_email, settings.excluded_mail_terms)
    if latest_email:
        print(f"Incremental sync: checking messages since {latest_email.date()}...", flush=True)
    else:
        print("Initial sync: checking Gmail history...", flush=True)
    for index, query in enumerate(queries, 1):
        print(f"Searching Gmail ({index}/{len(queries)})...", flush=True)
        ids.update(client.search_message_ids(query, settings.gmail_max_results))
    print(f"Found {len(ids)} candidate messages.", flush=True)
    messages = []
    for index, message_id in enumerate(ids, 1):
        messages.append(client.fetch_message(message_id))
        progress("Fetching messages", index, len(ids))
    if ids:
        print(flush=True)
    session = session_factory()
    try:
        print("Classifying and updating the local database...", flush=True)
        ingest_messages(session, messages, RuleBasedClassifier(), settings.no_response_days, excluded_terms=settings.excluded_mail_terms)
        refresh_statuses(session, settings.no_response_days)
    finally:
        session.close()
    print(f"Synchronized {len(ids)} candidate messages.")


def reclassify_stored_emails(settings, session_factory) -> None:
    """Reclassify stored email bodies using the current local rules."""
    with session_factory() as session:
        processed, changed = reclassify_emails(
            session,
            RuleBasedClassifier(),
            settings.no_response_days,
        )
    print(f"Reclassified {changed} of {processed} stored emails.")


def load_applications(session_factory):
    with session_factory() as session:
        return list(session.scalars(select(Application).order_by(Application.updated_at.desc())))


def list_applications(session_factory, status: str | None = None) -> None:
    for app in load_applications(session_factory):
        if not status or app.status == status:
            applied = app.applied_date.date() if app.applied_date else "-"
            last_contact = app.last_contact_date.date() if app.last_contact_date else "-"
            print(f"{app.company} | {app.position} | {applied} | {last_contact} | {app.status} | {app.contact_email or '-'} | {app.next_action or '-'}")


def show_stats(session_factory) -> None:
    applications = load_applications(session_factory)
    counts = status_counts(applications)
    print(f"Total applications: {len(applications)}")
    print(f"Applied (all stages): {cumulative_applied_count(applications)}")
    print("Current status:")
    for status, count in sorted(counts.items()):
        print(f"{status_label(status)}: {count}")


def export_applications(session_factory, output_path: str) -> None:
    applications = load_applications(session_factory)
    fields = ["company", "position", "applied_date", "last_contact_date", "status", "contact_email", "next_action", "source"]
    with open(output_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for app in applications:
            writer.writerow({field: getattr(app, field) for field in fields})
    print(f"Exported {len(applications)} applications to {output_path}.")


def generate_chart(session_factory, output_path: str) -> None:
    output = create_status_chart(load_applications(session_factory), output_path)
    print(f"Chart saved to {output.resolve()}")
