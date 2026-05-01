import json
from pathlib import Path

from backend.pipeline.filter.post_collection import post_collection_filter

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "golden.jsonl"


def test_golden_fixture_exists():
    assert FIXTURE.exists()


def test_golden_smoke_parse():
    count = 0
    for line in FIXTURE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        res = post_collection_filter(
            role_title=row["role_title"],
            description=row.get("description", ""),
            location_text=row.get("location", ""),
            employment_type="full-time",
            posted_at=None,
        )
        assert res.passed is True or res.reject_reason is not None
        count += 1
    assert count >= 100
