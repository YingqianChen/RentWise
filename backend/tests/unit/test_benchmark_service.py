from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.services.benchmark_service import BenchmarkService, load_benchmark_data
from tests.helpers import build_candidate, build_project, build_user


class BenchmarkServiceTests(TestCase):
    def setUp(self) -> None:
        self.service = BenchmarkService()
        self.user = build_user()
        self.project = build_project(self.user)

    def test_returns_available_benchmark_for_likely_sdu_candidate(self):
        candidate = build_candidate(self.project)
        candidate.raw_listing_text = "Wan Chai SDU room rental, rent 4800"
        candidate.combined_text = candidate.raw_listing_text

        result = self.service.build_for_candidate(candidate)

        self.assertEqual(result.status, "available")
        self.assertEqual(result.district, "Wan Chai")
        self.assertEqual(result.median_monthly_rent, 8000)
        self.assertTrue(result.disclaimer)

    def test_returns_not_applicable_for_non_sdu_candidate(self):
        candidate = build_candidate(self.project)
        candidate.raw_listing_text = "Entire furnished flat in Wan Chai"
        candidate.combined_text = candidate.raw_listing_text
        candidate.extracted_info.suspected_sdu = False
        candidate.extracted_info.sdu_detection_reason = "llm_non_sdu"

        result = self.service.build_for_candidate(candidate)

        self.assertEqual(result.status, "not_applicable")

    def test_uses_extraction_backed_sdu_hint_when_keywords_are_absent(self):
        candidate = build_candidate(self.project)
        candidate.raw_listing_text = "Compact rental in Wan Chai with shared kitchen"
        candidate.combined_text = candidate.raw_listing_text
        candidate.extracted_info.suspected_sdu = True
        candidate.extracted_info.sdu_detection_reason = "llm_sdu_hint"

        result = self.service.build_for_candidate(candidate)

        self.assertEqual(result.status, "available")

    def test_benchmark_data_file_has_expected_shape(self):
        data = load_benchmark_data()

        self.assertIn("wan chai", data)
        self.assertIn("source_period", data["wan chai"])
        self.assertIn("median_monthly_rent", data["wan chai"])
        self.assertIn("record_note", data["wan chai"])
        self.assertIn(data["sai kung"]["record_note"], {"normal", "fewer_than_10_records", "no_records"})
