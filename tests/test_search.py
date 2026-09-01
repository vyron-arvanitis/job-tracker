from datetime import datetime, timezone

from job_tracker.gmail.search import candidate_queries


def test_initial_search_has_no_date_boundary():
    assert all("after:" not in query for query in candidate_queries())


def test_incremental_search_uses_date_boundary():
    queries = candidate_queries(datetime(2026, 8, 21, 15, tzinfo=timezone.utc))
    assert all("after:2026/08/20" in query for query in queries)


def test_search_includes_french_application_terms():
    queries = candidate_queries()
    assert all('"candidature"' in query for query in queries)
    assert all('"retenus"' in query for query in queries)
