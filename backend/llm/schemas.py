from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MetricEntry(BaseModel):
    value: bool | None = None
    points: float = 0
    evidence: list[str] = Field(default_factory=list)


class LocationClassify(BaseModel):
    work_format: str = ""
    eu_compatible: bool = False
    confidence: float = 0
    evidence: list[str] = Field(default_factory=list)


class RoleSemantics(BaseModel):
    is_product: bool = False
    domain: str = "other"
    confidence: float = 0
    evidence: list[str] = Field(default_factory=list)


class ExtractScoring(BaseModel):
    """Структура по prometei_scoring_model §11 — группы как словари metric_key → MetricEntry."""

    critical: dict[str, Any] = Field(default_factory=dict)
    experience: dict[str, Any] = Field(default_factory=dict)
    skills: dict[str, Any] = Field(default_factory=dict)
    strategy_growth: dict[str, Any] = Field(default_factory=dict)
    company_context: dict[str, Any] = Field(default_factory=dict)
    bonuses: dict[str, Any] = Field(default_factory=dict)
    risks: list[str] = Field(default_factory=list)
    confidence: float = 0


class BatchExtractScoringResponse(BaseModel):
    """Пакетный ответ: ровно N блоков в том же порядке, что и входные JD."""

    items: list[ExtractScoring] = Field(default_factory=list)


class ExplainOut(BaseModel):
    why_kept: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
