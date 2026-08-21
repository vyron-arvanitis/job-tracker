from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from .models import Base


def make_session_factory(database_url: str):
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    # Lightweight schema migration for databases created before manual status
    # corrections were supported.
    application_columns = {column["name"] for column in inspect(engine).get_columns("applications")}
    if "status_override" not in application_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE applications ADD COLUMN status_override VARCHAR(50)"))
    email_columns = {column["name"] for column in inspect(engine).get_columns("emails")}
    if "is_sent" not in email_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE emails ADD COLUMN is_sent BOOLEAN NOT NULL DEFAULT 0"))
    if "contact_email" not in application_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE applications ADD COLUMN contact_email VARCHAR(320)"))
    return sessionmaker(bind=engine, expire_on_commit=False)
