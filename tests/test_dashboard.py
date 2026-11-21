"""Unit tests for Phase 7 - Results Dashboard filtering, metrics, and state handling."""

import pytest
from datetime import datetime, timezone
from src.models.schemas import (
    VerificationReport,
    ClaimVerificationResult,
    VerificationStatus,
    VerificationSourceCitation,
)
from tests.test_report_generator import create_comprehensive_test_report


class TestDashboardLogicAndFiltering:
    """Validate dashboard scorecard accuracy, filtering, search, and edge cases."""

    def test_dashboard_status_counts_match_report_metrics(self):
        report = create_comprehensive_test_report()

        actual_verified = sum(1 for r in report.results if r.status == VerificationStatus.VERIFIED)
        actual_inaccurate = sum(1 for r in report.results if r.status == VerificationStatus.INACCURATE)
        actual_false = sum(1 for r in report.results if r.status == VerificationStatus.FALSE)
        actual_unverified = sum(1 for r in report.results if r.status == VerificationStatus.UNVERIFIED)

        assert report.total_claims == 4
        assert report.verified_count == actual_verified == 1
        assert report.inaccurate_count == actual_inaccurate == 1
        assert report.false_count == actual_false == 1
        assert report.unverified_count == actual_unverified == 1
        assert (
            report.verified_count + report.inaccurate_count + report.false_count + report.unverified_count
            == report.total_claims
        )

    def test_filter_by_all_statuses(self):
        report = create_comprehensive_test_report()
        all_results = report.results
        assert len(all_results) == 4

        # Test individual status filtering logic
        for status, expected_count in [
            (VerificationStatus.VERIFIED, 1),
            (VerificationStatus.INACCURATE, 1),
            (VerificationStatus.FALSE, 1),
            (VerificationStatus.UNVERIFIED, 1),
        ]:
            filtered = [r for r in all_results if r.status == status]
            assert len(filtered) == expected_count
            assert all(r.status == status for r in filtered)

    def test_search_within_claims_and_explanations(self):
        report = create_comprehensive_test_report()

        # 1. Search by keyword in claim text
        kw1 = "gdp"
        matches1 = [
            r for r in report.results
            if kw1 in r.original_claim.lower() or kw1 in r.explanation.lower()
        ]
        assert len(matches1) == 1
        assert matches1[0].claim_id == "C001"

        # 2. Search by financial figure in correction
        kw2 = "12.4 billion"
        matches2 = [
            r for r in report.results
            if (r.corrected_information and kw2 in r.corrected_information.lower())
        ]
        assert len(matches2) == 1
        assert matches2[0].claim_id == "C002"

        # 3. Search by claim ID
        kw3 = "c003"
        matches3 = [r for r in report.results if r.claim_id.lower() == kw3]
        assert len(matches3) == 1
        assert matches3[0].status == VerificationStatus.FALSE

    def test_empty_search_result_state(self):
        report = create_comprehensive_test_report()
        kw_nonexistent = "quantum_crypto_blockchain_teleportation"
        matches = [
            r for r in report.results
            if (
                kw_nonexistent in r.original_claim.lower()
                or kw_nonexistent in r.explanation.lower()
            )
        ]
        assert len(matches) == 0

    def test_claims_with_multiple_sources_and_evidence_types(self):
        report = create_comprehensive_test_report()
        c001 = next(r for r in report.results if r.claim_id == "C001")

        assert len(c001.sources) == 2
        assert c001.sources[0].evidence_type == "supporting"
        assert c001.sources[1].evidence_type == "supporting"
        assert "mospi.gov.in" in c001.sources[0].url
        assert "rbi.org.in" in c001.sources[1].url

    def test_claim_without_sufficient_evidence_handling(self):
        report = create_comprehensive_test_report()
        c004 = next(r for r in report.results if r.claim_id == "C004")

        assert c004.status == VerificationStatus.UNVERIFIED
        assert c004.confidence == 0.0
        assert len(c004.sources) == 0
        assert c004.corrected_information is None
        assert "Insufficient public evidence" in c004.explanation

    def test_empty_report_dashboard_percentages_safety(self):
        empty_report = VerificationReport(
            document_name="zero_claims.pdf",
            total_pages=1,
            total_claims=0,
            verified_count=0,
            inaccurate_count=0,
            false_count=0,
            unverified_count=0,
            results=[],
        )

        tot = max(1, empty_report.total_claims)
        pct_v = round((empty_report.verified_count / tot) * 100, 1)
        pct_i = round((empty_report.inaccurate_count / tot) * 100, 1)
        pct_f = round((empty_report.false_count / tot) * 100, 1)
        pct_u = round((empty_report.unverified_count / tot) * 100, 1)

        assert pct_v == 0.0
        assert pct_i == 0.0
        assert pct_f == 0.0
        assert pct_u == 0.0
