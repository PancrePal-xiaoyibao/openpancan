"""
ClinicalTrials.gov API v2 client for pancreatic cancer trial search.

Docs: https://clinicaltrials.gov/api/v2/studies
Free public API — no authentication required.

Usage:
    client = ClinicalTrialsClient()
    trials = await client.search_pancreatic_cancer_trials(gene="KRAS")
    await client.aclose()
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

_DEFAULT_CONDITION = "pancreatic cancer"
_DEFAULT_STATUS = "RECRUITING,ACTIVE_NOT_RECRUITING"
_DEFAULT_PAGE_SIZE = 50
_REQUEST_TIMEOUT = 30.0
_MAX_RETRIES = 3
_RETRY_DELAY = 1.0


class ClinicalTrialsClient:
    """Async client for the ClinicalTrials.gov API v2."""

    def __init__(self, timeout: float = _REQUEST_TIMEOUT) -> None:
        base_url = settings.CLINICALTRIALS_API_BASE_URL
        self._client = httpx.AsyncClient(timeout=timeout, base_url=base_url)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def search_pancreatic_cancer_trials(
        self,
        gene: str | None = None,
        status: str = _DEFAULT_STATUS,
        page_size: int = _DEFAULT_PAGE_SIZE,
        max_pages: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Search active pancreatic cancer trials, optionally filtered by gene.

        Parameters
        ----------
        gene : str | None
            Gene symbol to filter trials (e.g. "KRAS", "BRCA1").
            If None, returns all pancreatic cancer trials.
        status : str
            Comma-separated recruitment status filter.
        page_size : int
            Results per page (max 100).
        max_pages : int
            Maximum number of pages to fetch.

        Returns
        -------
        list[dict]
            List of parsed trial dicts with keys:
            nct_id, title, phase, status, conditions, interventions,
            biomarker_match, url
        """
        all_trials: list[dict[str, Any]] = []
        next_page_token: str | None = None

        for page in range(max_pages):
            params = self._build_params(gene, status, page_size, next_page_token)
            raw_studies = await self._fetch_page(params)
            if not raw_studies:
                break

            parsed = [self._parse_study(s) for s in raw_studies]
            all_trials.extend(parsed)

            # Pagination: check if there's a next page token
            next_page_token = self._get_next_page_token(raw_studies)
            if not next_page_token:
                break

        logger.info(
            "ClinicalTrials.gov returned %d trials (gene=%s)",
            len(all_trials),
            gene or "any",
        )
        return all_trials

    async def search_trials_by_gene(
        self,
        gene: str,
        page_size: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Convenience: search pancreatic cancer trials matching a single gene.

        Parameters
        ----------
        gene : str
            Gene symbol (e.g. "BRCA1", "KRAS").

        Returns
        -------
        list[dict]
            Matched trials with biomarker_match populated from gene.
        """
        return await self.search_pancreatic_cancer_trials(gene=gene, page_size=page_size)

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_params(
        self,
        gene: str | None,
        status: str,
        page_size: int,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        """Build query parameters for the API request."""
        # Build the condition query
        condition = _DEFAULT_CONDITION
        if gene:
            # Search for the gene in the intervention or condition fields
            condition = f"{_DEFAULT_CONDITION} {gene}"

        params: dict[str, Any] = {
            "query.cond": condition,
            "filter.overallStatus": status,
            "pageSize": str(min(page_size, 100)),
            "fields": ",".join([
                "NCTId",
                "BriefTitle",
                "OfficialTitle",
                "Phase",
                "OverallStatus",
                "Condition",
                "InterventionName",
                "InterventionType",
                "EligibilityCriteria",
                "LeadSponsorName",
                "StartDate",
            ]),
            "format": "json",
            "markupFormat": "legacy",
        }

        if page_token:
            params["pageToken"] = page_token

        return params

    async def _fetch_page(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Fetch a single page of results with retry logic.

        Returns
        -------
        list[dict]
            Raw study objects from the API response, or empty list on failure.
        """
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                resp = await self._client.get("", params=params)
                resp.raise_for_status()
                data = resp.json()
                return data.get("studies", [])
            except httpx.HTTPStatusError as exc:
                logger.warning(
                    "ClinicalTrials.gov returned %d (attempt %d/%d)",
                    exc.response.status_code,
                    attempt,
                    _MAX_RETRIES,
                )
                if exc.response.status_code == 429:
                    # Rate limited — wait longer
                    await asyncio.sleep(_RETRY_DELAY * attempt * 2)
                elif exc.response.status_code >= 500:
                    await asyncio.sleep(_RETRY_DELAY * attempt)
                else:
                    # Client error — don't retry
                    break
            except (httpx.RequestError, httpx.DecodingError) as exc:
                logger.warning(
                    "ClinicalTrials.gov request failed (attempt %d/%d): %s",
                    attempt,
                    _MAX_RETRIES,
                    exc,
                )
                await asyncio.sleep(_RETRY_DELAY * attempt)

        logger.error("ClinicalTrials.gov fetch failed after %d attempts", _MAX_RETRIES)
        return []

    def _parse_study(self, study: dict[str, Any]) -> dict[str, Any]:
        """
        Parse a raw API study object into our standardised trial dict.

        Returns
        -------
        dict with keys:
            nct_id, title, phase, status, conditions, interventions,
            biomarker_match, url
        """
        protocol = study.get("protocolSection", {})
        id_module = protocol.get("identificationModule", {})
        status_module = protocol.get("statusModule", {})
        desc_module = protocol.get("descriptionModule", {})
        arms_module = protocol.get("armsInterventionsModule", {})
        eligibility = protocol.get("eligibilityModule", {})

        # NCT ID
        nct_id = id_module.get("nctId", "")

        # Title
        title = id_module.get("briefTitle", "") or id_module.get("officialTitle", "")

        # Phase
        phase_list = id_module.get("phase", [])
        if isinstance(phase_list, list):
            phase = "/".join(phase_list) if phase_list else "Not specified"
        else:
            phase = str(phase_list) if phase_list else "Not specified"

        # Status
        status = status_module.get("overallStatus", "Unknown")

        # Conditions
        conditions_list = id_module.get("conditions", [])
        conditions = " | ".join(conditions_list) if conditions_list else ""

        # Interventions
        interventions_list = arms_module.get("interventions", [])
        intervention_names = []
        for iv in interventions_list:
            name = iv.get("name", "")
            itype = iv.get("type", "")
            if name:
                intervention_names.append(f"{name} ({itype})" if itype else name)
        interventions = "; ".join(intervention_names)

        # Biomarker match — extract from eligibility criteria
        eligibility_text = eligibility.get("eligibilityCriteria", "")
        biomarker_match = self._extract_biomarker(eligibility_text, conditions)

        # URL
        url = f"https://clinicaltrials.gov/study/{nct_id}"

        return {
            "nct_id": nct_id,
            "title": title,
            "phase": phase,
            "status": status,
            "conditions": conditions,
            "interventions": interventions,
            "biomarker_match": biomarker_match,
            "url": url,
        }

    def _extract_biomarker(self, eligibility: str, conditions: str) -> str:
        """
        Extract biomarker keywords from eligibility criteria and conditions.

        Looks for known pancreatic cancer biomarker terms.
        """
        text = f"{eligibility} {conditions}".upper()

        # Known pancreatic cancer biomarkers (ordered by specificity)
        biomarkers = [
            ("KRAS G12C", "KRAS G12C mutation"),
            ("KRAS G12D", "KRAS G12D mutation"),
            ("KRAS G12V", "KRAS G12V mutation"),
            ("KRAS G12R", "KRAS G12R mutation"),
            ("KRAS", "KRAS mutation"),
            ("BRCA1", "BRCA1 mutation"),
            ("BRCA2", "BRCA2 mutation"),
            ("BRCA", "BRCA1/2 mutation"),
            ("PALB2", "PALB2 mutation"),
            ("MSI-H", "MSI-H/dMMR"),
            ("MICROSATELLITE INSTABILITY", "MSI-H/dMMR"),
            ("DMMR", "MSI-H/dMMR"),
            ("NTRK", "NTRK fusion"),
            ("HER2", "HER2 positive"),
            ("TP53", "TP53 mutation"),
            ("SMAD4", "SMAD4 mutation"),
            ("CDKN2A", "CDKN2A alteration"),
            ("PIK3CA", "PIK3CA mutation"),
            ("NRG1", "NRG1 fusion"),
            ("TMB-H", "TMB-H"),
            ("TUMOR MUTATIONAL BURDEN", "TMB-H"),
            ("MLH1", "Lynch syndrome (MLH1)"),
            ("MSH2", "Lynch syndrome (MSH2)"),
            ("MSH6", "Lynch syndrome (MSH6)"),
            ("PMS2", "Lynch syndrome (PMS2)"),
        ]

        found = []
        for keyword, label in biomarkers:
            # Skip broader matches if a more specific one was already found
            if any(label in f for f in found):
                continue
            if keyword in text:
                found.append(label)

        return ", ".join(found) if found else "Pancreatic cancer (broad eligibility)"

    def _get_next_page_token(self, studies: list[dict[str, Any]]) -> str | None:
        """Extract next page token from the response (not available in v2 API
        via the studies list — pagination uses count/totalCount)."""
        # ClinicalTrials.gov API v2 uses totalCount + pageSize for pagination
        # For simplicity, we just return None (single page fetch)
        # A production implementation would track totalCount
        return None


# ---------------------------------------------------------------------------
# Singleton for reuse across the application
# ---------------------------------------------------------------------------
_client: ClinicalTrialsClient | None = None


async def get_clinicaltrials_client() -> ClinicalTrialsClient:
    """Get or create the shared ClinicalTrials client."""
    global _client
    if _client is None:
        _client = ClinicalTrialsClient()
    return _client


async def close_clinicaltrials_client() -> None:
    """Close the shared client (call on app shutdown)."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
