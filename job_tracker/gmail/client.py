from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import base64
import re

@dataclass
class GmailMessage:
    message_id: str
    thread_id: str | None
    sender: str
    recipients: str | None
    subject: str
    sent_at: datetime
    body_text: str
    label_ids: list[str] = field(default_factory=list)

    @property
    def is_sent(self) -> bool:
        return "SENT" in self.label_ids

class GmailClient:
    def __init__(self, service): self.service = service
    @classmethod
    def from_credentials(cls, credentials):
        from googleapiclient.discovery import build
        return cls(build("gmail", "v1", credentials=credentials))
    def search_message_ids(self, query: str, max_results: int = 500) -> list[str]:
        ids, page_token = [], None
        while len(ids) < max_results:
            result = self.service.users().messages().list(userId="me", q=query, maxResults=min(100, max_results-len(ids)), pageToken=page_token).execute()
            ids.extend(item["id"] for item in result.get("messages", [])); page_token = result.get("nextPageToken")
            if not page_token: break
        return ids
    def fetch_message(self, message_id: str) -> GmailMessage:
        raw = self.service.users().messages().get(userId="me", id=message_id, format="full").execute()
        headers = {h["name"].lower(): h["value"] for h in raw.get("payload", {}).get("headers", [])}
        return GmailMessage(message_id, raw.get("threadId"), headers.get("from", ""), headers.get("to"), headers.get("subject", ""), _parse_date(headers.get("date"), raw.get("internalDate")), _extract_body(raw.get("payload", {})), raw.get("labelIds", []))

def _extract_body(payload: dict) -> str:
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        result = _extract_body(part)
        if result: return result
    if payload.get("mimeType") == "text/html" and payload.get("body", {}).get("data"):
        html = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
        return re.sub(r"<[^>]+>", " ", html).replace("&nbsp;", " ").strip()
    return ""

def _parse_date(value: str | None, internal: str | None) -> datetime:
    if value:
        try: return parsedate_to_datetime(value).astimezone(timezone.utc)
        except (TypeError, ValueError): pass
    return datetime.fromtimestamp(int(internal or 0) / 1000, tz=timezone.utc)
