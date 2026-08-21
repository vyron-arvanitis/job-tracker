from .client import GmailMessage
from job_tracker.classifier.base import EmailInput

def to_email_input(message: GmailMessage) -> EmailInput:
    return EmailInput(sender=message.sender, subject=message.subject, body_text=message.body_text, sent_at=message.sent_at)

