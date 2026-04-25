from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class OpportunityCreate(BaseModel):
    source_id: str
    external_id: str | None = None
    url: str | None = None
    title: str
    description: str | None = None
    company_name: str | None = None
    location: str | None = None
    remote_mode: str = "unknown"
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str = "USD"
    employment_type: str | None = None
    skills: list[str] = Field(default_factory=list)
    posted_at: datetime | None = None
    raw_data: dict[str, Any] = Field(default_factory=dict)
    tech_stack: list[str] = Field(default_factory=list)
    canonical_hash: str | None = None
    freshness_score: float = 1.0
    quality_score: float = 0.5
