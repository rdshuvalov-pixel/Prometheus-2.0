"""Генерация backend/tests/fixtures/golden.jsonl (100+ строк)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "backend" / "tests" / "fixtures" / "golden.jsonl"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for i in range(120):
        rows.append(
            {
                "id": f"g{i}",
                "role_title": "Senior Product Manager" if i % 3 else "Project Manager",
                "description": "Remote EU. Full-time. Roadmap ownership, discovery, B2B SaaS fintech."
                * (1 + (i % 2)),
                "location": "Remote Europe" if i % 2 == 0 else "US only",
                "expected_role": "product",
                "expected_score_min": 40,
                "expected_score_max": 100,
                "expected_decision": "Scored" if i % 3 else "Rejected",
                "expected_reject_reason": None if i % 3 else "not_product_role",
            }
        )
    with OUT.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Wrote {len(rows)} lines to {OUT}")


if __name__ == "__main__":
    main()
