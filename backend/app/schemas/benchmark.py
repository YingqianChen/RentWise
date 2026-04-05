"""Schemas for derived benchmark evidence."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class BenchmarkEvidence(BaseModel):
    """Structured SDU benchmark evidence derived from candidate context."""

    status: str
    district: Optional[str] = None
    source_period: Optional[str] = None
    median_monthly_rent: Optional[int] = None
    median_monthly_rent_per_sqm: Optional[int] = None
    record_note: Optional[str] = None
    disclaimer: Optional[str] = None
    fit_note: Optional[str] = None

