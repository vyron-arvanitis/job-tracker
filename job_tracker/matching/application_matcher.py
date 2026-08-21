from __future__ import annotations

import re
from sqlalchemy import select
from job_tracker.database.models import Application, Email

def normalize(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()

def find_application(session, company: str | None, position: str | None, thread_id: str | None) -> Application | None:
    if thread_id:
        match = session.scalar(select(Email.application_id).where(Email.gmail_thread_id == thread_id, Email.application_id.is_not(None)))
        if match:
            application = session.get(Application, match)
            # A shared thread is strong evidence, but never override a clearly
            # different extracted role.
            if not position or normalize(position) == application.position_key or not application.position_key:
                return application
    company_key, position_key = normalize(company), normalize(position)
    if not company_key or not position_key: return None
    return session.scalar(select(Application).where(Application.company_key == company_key, Application.position_key == position_key))
