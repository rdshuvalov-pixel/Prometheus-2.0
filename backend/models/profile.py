from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CandidateProfile(BaseModel):
    """Профиль кандидата из БД или seed."""

    id: UUID | None = None
    name: str = "Ruslan Shuvalov"
    profession: str = "Product Manager"
    search_keywords: list[str] = Field(default_factory=list)
    resume_md: str = ""
    interview_md: str = ""
    work_history_md: str = ""
    scoring_overrides: dict[str, Any] | None = None
    is_default: bool = True
