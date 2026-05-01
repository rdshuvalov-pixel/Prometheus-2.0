from datetime import datetime, timedelta, timezone

from backend.pipeline.dedup import dedup_check, fuzzy_same_role, reapply_title_suffix


def test_fuzzy():
    assert fuzzy_same_role("Senior Product Manager", "Sr Product Manager")


def test_dedup_duplicate():
    existing = [
        {
            "id": "1",
            "company": "Acme",
            "role_title": "Senior Product Manager",
            "posted_at": datetime.now(timezone.utc) - timedelta(days=2),
        }
    ]
    r = dedup_check(
        company="Acme",
        role_title="Sr Product Manager",
        existing_rows=existing,
        posted_at=datetime.now(timezone.utc),
    )
    assert r.is_duplicate


def test_reapply_suffix():
    s = reapply_title_suffix("PM Role")
    assert "[reapply" in s
