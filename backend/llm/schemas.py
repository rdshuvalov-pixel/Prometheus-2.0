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


class NormalizeVacancy(BaseModel):
    """TЗ normalize: extract structured vacancy fields. Unknown/missing must be null/unknown."""

    normalized_title: str | None = None
    seniority: str | None = None
    function: str | None = None
    domain: str | None = None
    industry: str | None = None
    employment_type: str | None = None
    work_format: str | None = None
    location_normalized: str | None = None
    country: str | None = None
    remote_allowed: bool | None = None
    hybrid_allowed: bool | None = None
    relocation_required: bool | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str | None = None
    english_required: bool | None = None
    product_type: str | None = None
    b2b_or_b2c: str | None = None
    ai_related: bool | None = None
    fintech_related: bool | None = None
    growth_related: bool | None = None
    monetization_related: bool | None = None
    platform_related: bool | None = None
    technical_depth: str | None = None
    management_scope: str | None = None
    must_have_requirements: list[str] = Field(default_factory=list)
    nice_to_have_requirements: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    positive_signals: list[str] = Field(default_factory=list)
    normalization_confidence: float | None = None
