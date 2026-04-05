"""Structured benchmark lookup for SDU median rent context."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

from ..db.models import CandidateListing
from ..schemas.benchmark import BenchmarkEvidence

DISCLAIMER = "For subdivided units only. General reference, not property-specific."
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "benchmark_sdu_rents.json"

_SDU_KEYWORDS = (
    "sdu",
    "subdivided unit",
    "sub-divided",
    "partitioned room",
    "room rental",
    "single room",
    "studio room",
    "\u528f\u623f",
    "\u5206\u9593",
    "\u5206\u79df",
    "\u5957\u623f",
    "\u96c5\u623f",
)


@lru_cache(maxsize=1)
def load_benchmark_data() -> dict[str, dict]:
    """Load structured SDU benchmark data from a versioned local file."""
    with DATA_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return {key.lower(): value for key, value in data.items()}


def _normalize_district(value: Optional[str]) -> Optional[str]:
    if not value or value.lower() == "unknown":
        return None
    return " ".join(value.strip().lower().split())


def _parse_number(value: Optional[str]) -> Optional[int]:
    if not value or value.lower() == "unknown":
        return None
    digits = re.sub(r"[^\d]", "", value)
    return int(digits) if digits else None


class BenchmarkService:
    """Provide narrow SDU district benchmark evidence."""

    def build_for_candidate(self, candidate: CandidateListing) -> BenchmarkEvidence:
        district = _normalize_district(candidate.extracted_info.district if candidate.extracted_info else None)
        if district is None:
            return BenchmarkEvidence(status="no_district")

        if not self._is_likely_sdu(candidate):
            return BenchmarkEvidence(
                status="not_applicable",
                district=candidate.extracted_info.district if candidate.extracted_info else None,
            )

        benchmark = load_benchmark_data().get(district)
        if benchmark is None:
            return BenchmarkEvidence(
                status="no_benchmark_record",
                district=candidate.extracted_info.district if candidate.extracted_info else None,
            )

        return BenchmarkEvidence(
            status="available",
            district=benchmark["district"],
            source_period=benchmark["source_period"],
            median_monthly_rent=benchmark["median_monthly_rent"],
            median_monthly_rent_per_sqm=benchmark["median_monthly_rent_per_sqm"],
            record_note=benchmark["record_note"],
            disclaimer=DISCLAIMER,
            fit_note=self._fit_note(candidate, benchmark["median_monthly_rent"]),
        )

    def _is_likely_sdu(self, candidate: CandidateListing) -> bool:
        text_parts = [
            candidate.raw_listing_text or "",
            candidate.raw_chat_text or "",
            candidate.raw_note_text or "",
            candidate.combined_text or "",
        ]
        text = " ".join(text_parts).lower()
        if any(keyword in text for keyword in _SDU_KEYWORDS):
            return True

        extracted = candidate.extracted_info
        if extracted is None:
            return False

        if extracted.suspected_sdu is True:
            return True
        if extracted.suspected_sdu is False:
            return False

        bedrooms = (extracted.bedrooms or "").lower()
        furnished = (extracted.furnished or "").lower()
        size_sqft = _parse_number(extracted.size_sqft)
        if "room" in bedrooms:
            return True
        if size_sqft is not None and size_sqft <= 180 and "shared" in furnished:
            return True
        return False

    def _fit_note(self, candidate: CandidateListing, benchmark_rent: Optional[int]) -> Optional[str]:
        quoted_rent = _parse_number(candidate.extracted_info.monthly_rent if candidate.extracted_info else None)
        if benchmark_rent is None or quoted_rent is None:
            return None

        gap = quoted_rent - benchmark_rent
        if abs(gap) <= 300:
            return "Quoted rent is close to this district SDU benchmark."
        if gap > 0:
            return "Quoted rent is above this district SDU benchmark."
        return "Quoted rent is below this district SDU benchmark."
