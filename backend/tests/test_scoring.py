from backend.scoring.engine import compute_score


def test_group_a_gate():
    feats = {
        "critical": {
            "product_management": {"value": False, "points": 0, "evidence": []},
            "work_format_fit": {"value": True, "points": 10, "evidence": []},
            "seniority_fit": {"value": True, "points": 10, "evidence": []},
            "full_time": {"value": True, "points": 5, "evidence": []},
            "location_fit": {"value": True, "points": 5, "evidence": []},
        },
        "experience": {},
        "skills": {},
        "strategy_growth": {},
        "company_context": {},
        "bonuses": {},
    }
    score, passed, _ = compute_score(feats)
    assert not passed
    assert score <= 49


def test_fin_weights_cap():
    """После усиления FinTech максимум очков по ключу ограничивается весом из YAML."""
    feats = {
        "critical": {
            "product_management": {"value": True, "points": 10, "evidence": []},
            "work_format_fit": {"value": True, "points": 10, "evidence": []},
            "seniority_fit": {"value": True, "points": 10, "evidence": []},
            "full_time": {"value": True, "points": 5, "evidence": []},
            "location_fit": {"value": True, "points": 5, "evidence": []},
        },
        "experience": {
            "fintech_or_ecommerce": {"points": 99, "evidence": []},
        },
        "skills": {},
        "strategy_growth": {},
        "company_context": {},
        "bonuses": {},
    }
    score, passed, bd = compute_score(feats)
    assert passed
    capped = bd["experience"]["fintech_or_ecommerce"]["points"]
    assert capped <= 7


def test_full_pass():
    feats = {
        "critical": {
            "product_management": {"value": True, "points": 10, "evidence": []},
            "work_format_fit": {"value": True, "points": 10, "evidence": []},
            "seniority_fit": {"value": True, "points": 10, "evidence": []},
            "full_time": {"value": True, "points": 5, "evidence": []},
            "location_fit": {"value": True, "points": 5, "evidence": []},
        },
        "experience": {
            "fintech_or_ecommerce": {"points": 6, "evidence": []},
            "b2b_saas": {"points": 5, "evidence": []},
            "ownership_roadmap_discovery": {"points": 5, "evidence": []},
            "responsibility_match": {"points": 5, "evidence": []},
            "task_match": {"points": 4, "evidence": []},
        },
        "skills": {},
        "strategy_growth": {},
        "company_context": {},
        "bonuses": {},
    }
    score, passed, bd = compute_score(feats)
    assert passed
    assert score >= 50
