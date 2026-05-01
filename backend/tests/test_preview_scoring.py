from backend.scoring.preview import compare_overrides


def test_preview_delta_on_override():
    out = compare_overrides({"experience": {"fintech_or_ecommerce": 10}})
    ids = {x["id"] for x in out["fixtures"]}
    assert "fintech_heavy" in ids
    row = next(x for x in out["fixtures"] if x["id"] == "fintech_heavy")
    assert row["delta"] != 0


def test_preview_group_a_unaffected_by_weights():
    out = compare_overrides({"experience": {"fintech_or_ecommerce": 10}})
    row = next(x for x in out["fixtures"] if x["id"] == "group_a_fail")
    assert row["delta"] == 0
