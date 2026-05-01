from backend.pipeline.filter.post_collection import post_collection_filter
from backend.pipeline.filter.search_time import passes_search_filters


def test_search_keywords():
    ok, _ = passes_search_filters(
        "Senior Product Manager",
        ["Product Manager", "Product Lead"],
    )
    assert ok


def test_post_collection_remote_eu():
    text = "Senior Product Manager\nRemote Europe full-time EU"
    res = post_collection_filter(
        role_title="Senior Product Manager",
        description=text,
        location_text=text,
        employment_type="full-time",
        posted_at=None,
    )
    assert res.passed or "date_unknown" in res.warnings
