from __future__ import annotations

import re

from .base import ClassificationResult, EmailClassifier, EmailInput

_REJECTION = re.compile(r"unfortunately|regret to inform|not proceed|leider|absage|nicht berücksichtigen|rejected", re.I)
_OFFER = re.compile(
    r"\b(?:pleased to offer|offer letter|job offer|employment offer)\b|"
    r"\b(?:vertragsangebot|arbeitsangebot|wir freuen uns, Ihnen .* anbieten)\b",
    re.I,
)
_TECH = re.compile(r"technical interview|coding interview|technical assessment|fachliches interview|technisches interview", re.I)
_ASSESSMENT = re.compile(r"coding assignment|take[- ]home|assessment|testaufgabe|online test", re.I)
_FINAL = re.compile(r"final interview|final stage|abschlussgespräch", re.I)
_HR = re.compile(r"interview|phone screen|screening|vorstellungsgespräch|gespräch", re.I)
_APPLIED = re.compile(r"thank you for applying|application received|your application|bewerbung erhalten|danke für ihre bewerbung", re.I)
_JOB = re.compile(r"application|applying|candidate|recruit|interview|career|position|role|bewerbung|bewerber|vorstellungsgespräch|stellenangebot|karriere", re.I)


class RuleBasedClassifier(EmailClassifier):
    def classify(self, email: EmailInput) -> ClassificationResult:
        text = f"{email.subject}\n{email.body_text}".strip()
        if not _JOB.search(text):
            return ClassificationResult(False, None, None, "unknown", 0.95)
        if _REJECTION.search(text): event, confidence = "rejection", .95
        elif _OFFER.search(text): event, confidence = "offer", .95
        elif _FINAL.search(text): event, confidence = "final_interview", .9
        elif _TECH.search(text): event, confidence = "technical_interview", .95
        elif _ASSESSMENT.search(text): event, confidence = "assessment", .9
        elif _APPLIED.search(text): event, confidence = "application_received", .9
        elif _HR.search(text): event, confidence = "hr_interview", .8
        else: event, confidence = "recruiter_contact", .55
        actions = {
            "application_received": "Wait for a response",
            "hr_interview": "Prepare for HR interview",
            "technical_interview": "Prepare for technical interview",
            "assessment": "Complete the assessment",
            "final_interview": "Prepare for final interview",
            "recruiter_contact": "Reply to recruiter",
        }
        return ClassificationResult(True, extract_company(email.sender, text), extract_position(text), event, confidence, actions.get(event))


def extract_company(sender: str, text: str) -> str | None:
    match = re.search(r"@([\w.-]+)", sender)
    if match:
        domain = match.group(1).split(".")[0]
        if domain not in {"gmail", "outlook", "yahoo", "hotmail"}: return domain.replace("-", " ").title()
    match = re.search(r"(?:at|bei|from|von)\s+([A-Z][\w&.-]+(?:\s+[A-Z][\w&.-]+)?)", text)
    return match.group(1).strip() if match else None


def extract_position(text: str) -> str | None:
    patterns = [r"(?:position|role|job|stelle)[:\s]+([^\n.!?]{3,100})", r"for the\s+([^\n.!?]{3,100})\s+position", r"für die Stelle als\s+([^\n.!?]{3,100})"]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            position = match.group(1).strip(" -–—")
            if position.lower() not in {"your application", "an update on your application", "your candidacy"}:
                return position
    return None
