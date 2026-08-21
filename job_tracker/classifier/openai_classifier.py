from __future__ import annotations

import json

from .base import ClassificationResult, EmailInput


class OpenAIClassifier:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def classify(self, email: EmailInput) -> ClassificationResult:
        prompt = ("Classify this recruiting email. Return JSON with keys "
                   "is_job_related, company, position, event_type, confidence, next_action. "
                   "event_type must be application_received, recruiter_contact, hr_interview, "
                   "technical_interview, assessment, final_interview, rejection, offer, withdrawal, unknown.\n"
                   f"From: {email.sender}\nSubject: {email.subject}\nBody:\n{email.body_text[:6000]}")
        response = self.client.chat.completions.create(model=self.model, temperature=0, response_format={"type":"json_object"}, messages=[{"role":"user", "content":prompt}])
        return ClassificationResult(**json.loads(response.choices[0].message.content))
