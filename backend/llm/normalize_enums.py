"""Enum coercion for NormalizeVacancy per docs/llm_prompt.md §9–10."""

from __future__ import annotations

from backend.llm.schemas import NormalizeVacancy

SENIORITY = frozenset(
    {
        "Intern",
        "Junior",
        "Middle",
        "Senior",
        "Lead",
        "Principal",
        "Head",
        "Director",
        "VP",
        "C-level",
        "Unknown",
    }
)

FUNCTION = frozenset(
    {
        "Product Management",
        "Product Marketing",
        "Growth",
        "Data",
        "Engineering",
        "Design",
        "Operations",
        "Sales",
        "Marketing",
        "Customer Success",
        "Other",
        "Unknown",
    }
)

WORK_FORMAT = frozenset({"Remote", "Hybrid", "Onsite", "Flexible", "Unknown"})

TECHNICAL_DEPTH = frozenset({"Low", "Medium", "High", "Unknown"})

B2B_OR_B2C = frozenset({"B2B", "B2C", "B2B2C", "Marketplace", "Internal", "Unknown"})


def coerce_normalize_enums(model: NormalizeVacancy) -> tuple[NormalizeVacancy, bool]:
    """Invalid enum strings become Unknown; returns (possibly updated model, coerced?)."""
    coerced = False
    data = model.model_dump()

    checks: list[tuple[str, frozenset[str]]] = [
        ("seniority", SENIORITY),
        ("function", FUNCTION),
        ("work_format", WORK_FORMAT),
        ("technical_depth", TECHNICAL_DEPTH),
        ("b2b_or_b2c", B2B_OR_B2C),
    ]

    for key, allowed in checks:
        val = data.get(key)
        if val is None:
            continue
        v = str(val).strip()
        if v and v not in allowed:
            data[key] = "Unknown"
            coerced = True

    return NormalizeVacancy.model_validate(data), coerced
