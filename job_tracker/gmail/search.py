from datetime import datetime, timedelta

SEARCH_TERMS = ["application", "applied", "thank you for applying", "application received", "your application", "candidate", "recruiting", "recruiter", "talent acquisition", "interview", "technical interview", "coding interview", "assessment", "next step", "offer", "unfortunately", "regret to inform", "Bewerbung", "Bewerbung erhalten", "Vorstellungsgespräch", "Gespräch", "nächster Schritt", "Absage", "leider", "Stellenangebot", "Karriere"]

def candidate_queries(since: datetime | None = None, excluded_terms: tuple[str, ...] = ()) -> list[str]:
    terms = " OR ".join(f'"{term}"' for term in SEARCH_TERMS)
    base = f"({terms}) -category:promotions -category:social"
    if excluded_terms:
        base += " " + " ".join(f'-"{term}"' for term in excluded_terms)
    if since:
        # Include a one-day overlap to protect against timezone/date-boundary
        # differences. Existing Gmail IDs are skipped during ingestion.
        boundary = (since - timedelta(days=1)).strftime("%Y/%m/%d")
        base = f"after:{boundary} {base}"
    return [f"in:anywhere {base}", f"in:sent {base}"]
