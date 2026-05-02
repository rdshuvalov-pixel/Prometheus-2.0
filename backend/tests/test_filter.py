from backend.pipeline.filter.post_collection import post_collection_filter
from backend.pipeline.filter.search_time import passes_search_filters
from backend.pipeline.normalize.location import hybrid_location_blacklisted


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


def test_hybrid_location_blacklisted_cyprus():
    assert hybrid_location_blacklisted("Senior PM hybrid Cyprus EU") == "Cyprus"


def test_hybrid_location_blacklisted_georgia():
    assert hybrid_location_blacklisted("Product hybrid Tbilisi") == "Tbilisi"


def test_hybrid_location_blacklisted_requires_hybrid_word():
    assert hybrid_location_blacklisted("Remote Cyprus EU") is None


def test_post_collection_remote_hybrid_cyprus_rejected():
    text = "Senior Product Manager\nRemote Europe hybrid work Cyprus\nfull-time"
    res = post_collection_filter(
        role_title="Senior Product Manager",
        description=text,
        location_text=text,
        employment_type="full-time",
        posted_at=None,
    )
    assert not res.passed
    assert res.reject_reason == "hybrid_outside_lisbon"


def test_post_collection_hybrid_lisbon_passes():
    text = "Senior Product Manager\nRemote EU hybrid Lisbon\nfull-time"
    res = post_collection_filter(
        role_title="Senior Product Manager",
        description=text,
        location_text=text,
        employment_type="full-time",
        posted_at=None,
    )
    assert res.reject_reason != "hybrid_outside_lisbon"
    assert res.passed or "date_unknown" in res.warnings
