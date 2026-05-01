"""Парсинг search_targets.md → backend/sources/targets.yaml."""

from __future__ import annotations

from pathlib import Path

import yaml

_REPO = Path(__file__).resolve().parents[2]
_MD = _REPO / "search_targets.md"
_OUT = _REPO / "backend" / "sources" / "targets.yaml"


def detect_ats(url: str) -> str | None:
    u = url.lower()
    if "lever.co" in u:
        return "lever"
    if "greenhouse.io" in u:
        return "greenhouse"
    if "ashbyhq.com" in u:
        return "ashby"
    if "workable.com" in u:
        return "workable"
    if "breezy.hr" in u:
        return "breezy"
    if "teamtailor.com" in u:
        return "teamtailor"
    if "myworkdayjobs.com" in u:
        return "workday"
    return None


def parse_table_rows(md: str, tier: str) -> list[dict]:
    rows: list[dict] = []
    for line in md.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|")]
        parts = [p for p in parts if p]
        if len(parts) < 2:
            continue
        if parts[0].lower() in ("компания", "company", "платформа"):
            continue
        if set(parts[0]) <= {"-", ":"}:
            continue
        company, url = parts[0], parts[1]
        if not url.startswith("http"):
            continue
        rows.append(
            {
                "company": company,
                "url": url,
                "tier": tier,
                "ats_type": detect_ats(url),
            }
        )
    return rows


def main() -> None:
    if not _MD.exists():
        raise SystemExit(f"Нет файла {_MD}")
    text = _MD.read_text(encoding="utf-8")
    tiers_data: list[dict] = []

    def extract_section(header: str, tier_label: str) -> None:
        idx = text.find(header)
        if idx < 0:
            return
        chunk = text[idx : idx + 80000]
        end = chunk.find("\n## ")
        if end > 0:
            chunk = chunk[:end]
        tiers_data.extend(parse_table_rows(chunk, tier_label))

    extract_section("## Tier 1", "1")
    extract_section("## Tier 2", "2")
    extract_section("## Tier 3", "3")
    extract_section("## Tier 4", "4")

    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(yaml.safe_dump({"targets": tiers_data}, allow_unicode=True), encoding="utf-8")
    print(f"Wrote {len(tiers_data)} targets to {_OUT}")


if __name__ == "__main__":
    main()
