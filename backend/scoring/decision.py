from __future__ import annotations


def vacancy_status_from_score(score: int, group_a_passed: bool) -> tuple[str, str | None]:
    """Статус вакансии и reject_reason если отсечка."""
    if not group_a_passed or score < 50:
        return "Rejected", "below_threshold"
    return "Scored", None
