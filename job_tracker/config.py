from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///job_tracker.db"
    credentials_file: Path = Path("credentials.json")
    token_file: Path = Path("token.json")
    no_response_days: int = 14
    gmail_max_results: int = 500
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    excluded_mail_terms: tuple[str, ...] = ("lmu", "mpq", "studienberatung")


def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///job_tracker.db"),
        credentials_file=Path(os.getenv("CREDENTIALS_FILE", "credentials.json")),
        token_file=Path(os.getenv("TOKEN_FILE", "token.json")),
        no_response_days=int(os.getenv("NO_RESPONSE_DAYS", "14")),
        gmail_max_results=int(os.getenv("GMAIL_MAX_RESULTS", "500")),
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        excluded_mail_terms=tuple(term.strip() for term in os.getenv("EXCLUDED_MAIL_TERMS", "lmu,mpq,studienberatung").split(",") if term.strip()),
    )
