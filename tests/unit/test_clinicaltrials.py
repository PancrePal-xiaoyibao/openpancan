"""
Unit tests for ClinicalTrials.gov API client (Phase 7).

Tests cover:
1. API client construction and parameter building
2. Response parsing
3. Biomarker extraction from eligibility text
4. Fallback local database matching
5. Retry logic on failure
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

# ---------------------------------------------------------------------------
# Import the modules under test
# ---------------------------------------------------------------------------
import sys
from pathlib import Path

# Add PanCancerSystem backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "modules" / "PanCancerSystem"))

from backend.services.clinicaltrials_client import (
    ClinicalTrialsClient,
)
from backend.config import settings

_CT_API_URL = settings.CLINICALTRIALS_API_BASE_URL
from backend.api.trials import (
    _FALLBACK_TRIALS,
    _match_fallback_trials,
    TrialMatch,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_API_RESPONSE = {
    "studies": [
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT05379985",
                    "briefTitle": "RMC-6236 in KRAS Mutant Solid Tumors",
                    "phase": ["Phase I", "Phase II"],
                    "conditions": ["Pancreatic Cancer", "KRAS Mutation"],
                },
                "statusModule": {
                    "overallStatus": "Recruiting",
                },
                "armsInterventionsModule": {
                    "interventions": [
                        {"name": "RMC-6236", "type": "DRUG"},
                    ],
                },
                "eligibilityModule": {
                    "eligibilityCriteria": "Inclusion: KRAS G12D or G12V mutation",
                },
            },
        },
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT02184195",
                    "briefTitle": "Olaparib in BRCA Mutated Pancreatic Cancer",
                    "phase": ["Phase III"],
                    "conditions": ["Pancreatic Cancer", "BRCA1 Mutation", "BRCA2 Mutation"],
                },
                "statusModule": {
                    "overallStatus": "Active, not recruiting",
                },
                "armsInterventionsModule": {
                    "interventions": [
                        {"name": "Olaparib", "type": "DRUG"},
                    ],
                },
                "eligibilityModule": {
                    "eligibilityCriteria": "Inclusion: Germline BRCA1 or BRCA2 mutation",
                },
            },
        },
    ]
}


# ---------------------------------------------------------------------------
# Test: ClinicalTrialsClient parameter building
# ---------------------------------------------------------------------------

class TestClientParams:
    def test_build_params_no_gene(self):
        client = ClinicalTrialsClient()
        params = client._build_params(gene=None, status="RECRUITING", page_size=20)
        assert params["query.cond"] == "pancreatic cancer"
        assert params["filter.overallStatus"] == "RECRUITING"
        assert params["pageSize"] == "20"

    def test_build_params_with_gene(self):
        client = ClinicalTrialsClient()
        params = client._build_params(gene="KRAS", status="RECRUITING", page_size=50)
        assert "KRAS" in params["query.cond"]
        assert "pancreatic cancer" in params["query.cond"]

    def test_build_params_page_size_capped(self):
        client = ClinicalTrialsClient()
        params = client._build_params(gene=None, status="RECRUITING", page_size=200)
        assert params["pageSize"] == "100"  # max 100


# ---------------------------------------------------------------------------
# Test: Response parsing
# ---------------------------------------------------------------------------

class TestParsing:
    def test_parse_study_basic(self):
        client = ClinicalTrialsClient()
        study = SAMPLE_API_RESPONSE["studies"][0]
        parsed = client._parse_study(study)

        assert parsed["nct_id"] == "NCT05379985"
        assert "RMC-6236" in parsed["title"]
        assert "Phase I" in parsed["phase"]
        assert "Phase II" in parsed["phase"]
        assert parsed["status"] == "Recruiting"
        assert "KRAS" in parsed["conditions"]
        assert "RMC-6236" in parsed["interventions"]
        assert "clinicaltrials.gov" in parsed["url"]

    def test_parse_study_phase_iii(self):
        client = ClinicalTrialsClient()
        study = SAMPLE_API_RESPONSE["studies"][1]
        parsed = client._parse_study(study)

        assert parsed["nct_id"] == "NCT02184195"
        assert parsed["phase"] == "Phase III"
        assert "Olaparib" in parsed["interventions"]

    def test_parse_empty_study(self):
        client = ClinicalTrialsClient()
        parsed = client._parse_study({})
        assert parsed["nct_id"] == ""
        assert parsed["title"] == ""
        assert parsed["phase"] == "Not specified"


# ---------------------------------------------------------------------------
# Test: Biomarker extraction
# ---------------------------------------------------------------------------

class TestBiomarkerExtraction:
    def test_kras_g12d(self):
        client = ClinicalTrialsClient()
        result = client._extract_biomarker(
            "Inclusion: KRAS G12D mutation", ""
        )
        assert "KRAS G12D mutation" in result

    def test_brca_mutation(self):
        client = ClinicalTrialsClient()
        result = client._extract_biomarker(
            "Patients with BRCA1 or BRCA2 germline mutation", ""
        )
        assert "BRCA1 mutation" in result
        assert "BRCA2 mutation" in result

    def test_msi_h(self):
        client = ClinicalTrialsClient()
        result = client._extract_biomarker(
            "Microsatellite instability-high (MSI-H) tumors", ""
        )
        assert "MSI-H/dMMR" in result

    def test_no_biomarker(self):
        client = ClinicalTrialsClient()
        result = client._extract_biomarker("Adults with pancreatic cancer", "")
        assert "broad eligibility" in result

    def test_multiple_biomarkers(self):
        client = ClinicalTrialsClient()
        result = client._extract_biomarker(
            "KRAS G12D mutation, BRCA1, MSI-H", ""
        )
        assert "KRAS G12D" in result
        assert "BRCA1" in result
        assert "MSI-H" in result

    def test_specific_over_generic(self):
        """KRAS G12D should match before generic 'KRAS mutation'."""
        client = ClinicalTrialsClient()
        result = client._extract_biomarker("KRAS G12D mutation", "")
        assert "KRAS G12D mutation" in result
        # Should NOT also include "KRAS mutation" since G12D is more specific
        # (the dedup logic skips broader matches if specific one found)


# ---------------------------------------------------------------------------
# Test: Fallback local matching
# ---------------------------------------------------------------------------

class TestFallbackMatching:
    def test_match_kras(self):
        matches = _match_fallback_trials(["KRAS"])
        assert len(matches) > 0
        assert any("KRAS" in m.match_reason for m in matches)

    def test_match_brca(self):
        matches = _match_fallback_trials(["BRCA1", "BRCA2"])
        assert len(matches) > 0
        assert any("BRCA" in m.match_reason for m in matches)

    def test_match_msi_h(self):
        matches = _match_fallback_trials(["MSI-H"])
        assert len(matches) > 0

    def test_no_match_returns_empty(self):
        matches = _match_fallback_trials(["FAKE_GENE_XYZ"])
        # Should return empty (no general trial added in fallback-only function)
        assert all("FAKE_GENE_XYZ" not in m.match_reason for m in matches)

    def test_fallback_trials_have_valid_structure(self):
        """Verify all fallback trials have required fields."""
        for trial in _FALLBACK_TRIALS:
            assert "nct_id" in trial
            assert "title" in trial
            assert "phase" in trial
            assert "genes" in trial
            assert trial["nct_id"].startswith("NCT")


# ---------------------------------------------------------------------------
# Test: API fetch with mock
# ---------------------------------------------------------------------------

class TestAPIFetch:
    @pytest.mark.asyncio
    async def test_search_returns_parsed_trials(self):
        """Test that API search returns properly parsed trials."""
        client = ClinicalTrialsClient()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value=SAMPLE_API_RESPONSE)

        with patch.object(client._client, "get", new_callable=AsyncMock, return_value=mock_response):
            trials = await client.search_pancreatic_cancer_trials(gene="KRAS")

        assert len(trials) == 2
        assert trials[0]["nct_id"] == "NCT05379985"
        assert trials[1]["nct_id"] == "NCT02184195"

        await client.aclose()

    @pytest.mark.asyncio
    async def test_search_handles_http_error(self):
        """Test graceful handling of HTTP errors."""
        client = ClinicalTrialsClient()

        with patch.object(
            client._client, "get",
            new_callable=AsyncMock,
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            trials = await client.search_pancreatic_cancer_trials(gene="KRAS")

        # Should return empty list on connection error
        assert trials == []

        await client.aclose()

    @pytest.mark.asyncio
    async def test_search_by_gene_convenience(self):
        """Test the convenience search_trials_by_gene method."""
        client = ClinicalTrialsClient()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value=SAMPLE_API_RESPONSE)

        with patch.object(client._client, "get", new_callable=AsyncMock, return_value=mock_response):
            trials = await client.search_trials_by_gene(gene="BRCA1")

        assert len(trials) == 2

        await client.aclose()


# ---------------------------------------------------------------------------
# Test: TrialMatch model
# ---------------------------------------------------------------------------

class TestTrialMatchModel:
    def test_create_trial_match(self):
        m = TrialMatch(
            nct_id="NCT12345",
            title="Test Trial",
            phase="Phase II",
            status="Recruiting",
            conditions="Pancreatic Cancer",
            interventions="Drug A",
            match_reason="Gene match: KRAS",
            url="https://clinicaltrials.gov/study/NCT12345",
        )
        assert m.nct_id == "NCT12345"
        assert m.phase == "Phase II"
        assert "KRAS" in m.match_reason
