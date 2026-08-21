from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class EmailInput:
    sender: str
    subject: str
    body_text: str
    sent_at: object | None = None


@dataclass
class ClassificationResult:
    is_job_related: bool
    company: str | None
    position: str | None
    event_type: str
    confidence: float
    next_action: str | None = None


class EmailClassifier(Protocol):
    def classify(self, email: EmailInput) -> ClassificationResult: ...
