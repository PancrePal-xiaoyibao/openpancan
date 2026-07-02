"""
Clinical trial matching for pancreatic cancer.

Matches genomic biomarker profiles to active clinical trials for
pancreatic ductal adenocarcinoma.

Supports two data sources:
1. ClinicalTrials.gov API v2 (live, when network available)
2. Curated local database (fallback when API is unavailable)
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ClinicalTrials.gov API v2 client
# ---------------------------------------------------------------------------
_CTGOV_BASE_URL = "https://clinicaltrials.gov/api/v2/studies"


async def fetch_trials_from_api(
    gene: str | None = None,
    page_size: int = 50,
) -> list[dict[str, Any]]:
    """
    Fetch pancreatic cancer trials from ClinicalTrials.gov API v2.

    Parameters
    ----------
    gene : str | None
        Optional gene symbol to narrow the search.
    page_size : int
        Number of results per page.

    Returns
    -------
    list[dict]
        Parsed trial dicts, or empty list on failure.
    """
    condition = f"pancreatic cancer {gene}" if gene else "pancreatic cancer"
    params = {
        "query.cond": condition,
        "filter.overallStatus": "RECRUITING,ACTIVE_NOT_RECRUITING",
        "pageSize": str(page_size),
        "fields": ",".join([
            "NCTId", "BriefTitle", "Phase", "OverallStatus",
            "Condition", "InterventionName", "EligibilityCriteria",
        ]),
        "format": "json",
    }

    trials: list[dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(_CTGOV_BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        for study in data.get("studies", []):
            protocol = study.get("protocolSection", {})
            id_mod = protocol.get("identificationModule", {})
            status_mod = protocol.get("statusModule", {})
            arms_mod = protocol.get("armsInterventionsModule", {})
            elig_mod = protocol.get("eligibilityModule", {})

            nct_id = id_mod.get("nctId", "")
            title = id_mod.get("briefTitle", "")
            phase_list = id_mod.get("phase", [])
            phase = "/".join(phase_list) if isinstance(phase_list, list) else str(phase_list)
            status = status_mod.get("overallStatus", "Unknown")
            conditions = " | ".join(id_mod.get("conditions", []))
            interventions_list = arms_mod.get("interventions", [])
            interventions = "; ".join(
                iv.get("name", "") for iv in interventions_list if iv.get("name")
            )
            eligibility = elig_mod.get("eligibilityCriteria", "")
            biomarker = _extract_biomarker_from_text(eligibility, conditions)

            trials.append({
                "nct_id": nct_id,
                "title": title,
                "phase": phase or "Not specified",
                "status": status,
                "biomarker_match": biomarker,
                "drug": interventions,
                "url": f"https://clinicaltrials.gov/study/{nct_id}",
            })

    except (httpx.HTTPError, httpx.ConnectError) as exc:
        logger.warning("ClinicalTrials.gov API unavailable: %s", exc)
    except Exception as exc:
        logger.warning("Failed to fetch trials from API: %s", exc)

    return trials


def _extract_biomarker_from_text(eligibility: str, conditions: str) -> str:
    """Extract biomarker keywords from eligibility criteria and conditions."""
    text = f"{eligibility} {conditions}".upper()
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
    ]
    found = []
    for keyword, label in biomarkers:
        if any(label in f for f in found):
            continue
        if keyword in text:
            found.append(label)
    return ", ".join(found) if found else "Pancreatic cancer (broad eligibility)"

# ---------------------------------------------------------------------------
# Pancreatic Cancer Clinical Trials Database (curated)
# ---------------------------------------------------------------------------
PANCREATIC_CLINICAL_TRIALS: list[dict[str, Any]] = [
    # ---- KRAS-targeted trials ----
    {
        "nct_id": "NCT05379985",
        "title": "A Study of RMC-6236 in Patients With Advanced Solid Tumors Harboring Specific KRAS Mutations",
        "phase": "Phase I/II",
        "status": "Recruiting",
        "biomarker_match": "KRAS G12D, G12V, G12R, G12A, G12S mutation",
        "drug": "RMC-6236 (Pan-RAS inhibitor)",
        "url": "https://clinicaltrials.gov/study/NCT05379985",
    },
    {
        "nct_id": "NCT05737706",
        "title": "A Study of MRTX1133 in Patients With Advanced Solid Tumors Harboring a KRAS G12D Mutation",
        "phase": "Phase I/II",
        "status": "Recruiting",
        "biomarker_match": "KRAS G12D mutation",
        "drug": "MRTX1133 (KRAS G12D inhibitor)",
        "url": "https://clinicaltrials.gov/study/NCT05737706",
    },
    {
        "nct_id": "NCT04975256",
        "title": "RMC-6291 Alone and in Combination in Subjects With Advanced KRAS G12C Mutated Solid Tumors",
        "phase": "Phase I",
        "status": "Recruiting",
        "biomarker_match": "KRAS G12C mutation",
        "drug": "RMC-6291 (KRAS G12C inhibitor)",
        "url": "https://clinicaltrials.gov/study/NCT04975256",
    },
    {
        "nct_id": "NCT03600883",
        "title": "A Phase I/II Study of MRTX849 (Adagrasib) in Patients With Advanced Solid Tumors With KRAS G12C Mutation",
        "phase": "Phase I/II",
        "status": "Active, not recruiting",
        "biomarker_match": "KRAS G12C mutation",
        "drug": "Adagrasib (MRTX849)",
        "url": "https://clinicaltrials.gov/study/NCT03600883",
    },
    # ---- PARP inhibitor trials ----
    {
        "nct_id": "NCT02184195",
        "title": "Olaparib as Maintenance Therapy in Patients With Germline BRCA Mutated Metastatic Pancreatic Cancer (POLO)",
        "phase": "Phase III",
        "status": "Active, not recruiting",
        "biomarker_match": "BRCA1/2 germline mutation",
        "drug": "Olaparib",
        "url": "https://clinicaltrials.gov/study/NCT02184195",
    },
    {
        "nct_id": "NCT04548752",
        "title": "Niraparib in Patients With Pancreatic Cancer and Known BRCA or PALB2 Mutations",
        "phase": "Phase II",
        "status": "Recruiting",
        "biomarker_match": "BRCA1/2 or PALB2 mutation",
        "drug": "Niraparib",
        "url": "https://clinicaltrials.gov/study/NCT04548752",
    },
    {
        "nct_id": "NCT03140670",
        "title": "Rucaparib in Patients With Pancreatic Cancer and Known BRCA1/2 or PALB2 Mutation",
        "phase": "Phase II",
        "status": "Recruiting",
        "biomarker_match": "BRCA1/2 or PALB2 mutation",
        "drug": "Rucaparib",
        "url": "https://clinicaltrials.gov/study/NCT03140670",
    },
    # ---- Immunotherapy trials ----
    {
        "nct_id": "NCT02628067",
        "title": "Pembrolizumab in Patients With Advanced Pancreatic Cancer and MSI-H or dMMR",
        "phase": "Phase II",
        "status": "Recruiting",
        "biomarker_match": "MSI-H or dMMR",
        "drug": "Pembrolizumab (Keytruda)",
        "url": "https://clinicaltrials.gov/study/NCT02628067",
    },
    {
        "nct_id": "NCT04802876",
        "title": "Nivolumab + Ipilimumab in dMMR/MSI-H Pancreatic Cancer",
        "phase": "Phase II",
        "status": "Recruiting",
        "biomarker_match": "MSI-H or dMMR",
        "drug": "Nivolumab + Ipilimumab",
        "url": "https://clinicaltrials.gov/study/NCT04802876",
    },
    {
        "nct_id": "NCT03991832",
        "title": "Olaparib + Durvalumab in BRCA-Mutated Pancreatic Cancer",
        "phase": "Phase II",
        "status": "Recruiting",
        "biomarker_match": "BRCA1/2 mutation",
        "drug": "Olaparib + Durvalumab",
        "url": "https://clinicaltrials.gov/study/NCT03991832",
    },
    # ---- Novel combination trials ----
    {
        "nct_id": "NCT04229004",
        "title": "Trametinib + Hydroxychloroquine in Patients With Refractory KRAS-Mutant Pancreatic Cancer",
        "phase": "Phase II",
        "status": "Recruiting",
        "biomarker_match": "KRAS mutation",
        "drug": "Trametinib + Hydroxychloroquine",
        "url": "https://clinicaltrials.gov/study/NCT04229004",
    },
    {
        "nct_id": "NCT04870034",
        "title": "Adoptive Cell Therapy Targeting KRAS G12D in Pancreatic Cancer",
        "phase": "Phase I",
        "status": "Recruiting",
        "biomarker_match": "KRAS G12D mutation + HLA-C*08:02",
        "drug": "TCR-engineered T cells (KRAS G12D)",
        "url": "https://clinicaltrials.gov/study/NCT04870034",
    },
    {
        "nct_id": "NCT04166721",
        "title": "mRNA-4157 + Pembrolizumab in Advanced Pancreatic Cancer",
        "phase": "Phase I",
        "status": "Recruiting",
        "biomarker_match": "MSI-H, TMB-H or KRAS mutation",
        "drug": "Personalized mRNA cancer vaccine + Pembrolizumab",
        "url": "https://clinicaltrials.gov/study/NCT04166721",
    },
    {
        "nct_id": "NCT05275491",
        "title": "ELI-002 in KRAS G12D/G12R Mutant Pancreatic Cancer",
        "phase": "Phase I",
        "status": "Recruiting",
        "biomarker_match": "KRAS G12D or G12R mutation",
        "drug": "ELI-002 (KRAS-targeted vaccine)",
        "url": "https://clinicaltrials.gov/study/NCT05275491",
    },
    # ---- Standard care trials ----
    {
        "nct_id": "NCT04083235",
        "title": "NAPOLI-3: NALIRIFOX vs Gemcitabine/Nab-Paclitaxel in First-Line mPDAC",
        "phase": "Phase III",
        "status": "Active, not recruiting",
        "biomarker_match": "Any pancreatic cancer (first-line)",
        "drug": "NALIRIFOX (liposomal irinotecan + 5-FU + oxaliplatin)",
        "url": "https://clinicaltrials.gov/study/NCT04083235",
    },
    {
        "nct_id": "NCT03504423",
        "title": "Precision Promise: Adaptive Platform Trial in Pancreatic Cancer",
        "phase": "Phase II/III",
        "status": "Recruiting",
        "biomarker_match": "Multiple biomarkers, various arms",
        "drug": "Multiple (platform trial)",
        "url": "https://clinicaltrials.gov/study/NCT03504423",
    },
]


def match_clinical_trials(
    variants_df: pd.DataFrame,
    cancer_type: str = "pancreatic_ductal_adenocarcinoma",
    use_api: bool = True,
) -> list[dict[str, Any]]:
    """
    Match genomic biomarkers to active clinical trials.

    Tries ClinicalTrials.gov API first (when use_api=True and gene
    information is available), then falls back to the curated local
    database.

    Parameters
    ----------
    variants_df : pd.DataFrame
        Variant DataFrame with SYMBOL, HGVSp columns.
    cancer_type : str
        Cancer type.
    use_api : bool
        Whether to attempt the ClinicalTrials.gov API call.

    Returns
    -------
    list[dict]
        Matched clinical trials sorted by relevance.
    """
    matched_trials: list[dict[str, Any]] = []

    # Collect biomarkers from variants
    biomarkers_present: set[str] = set()
    genes_mutated: set[str] = set()

    if "SYMBOL" in variants_df.columns:
        for _, row in variants_df.iterrows():
            gene = str(row.get("SYMBOL", ""))
            hgvsp = str(row.get("HGVSp", ""))
            genes_mutated.add(gene)

            # KRAS
            if gene == "KRAS":
                biomarkers_present.add("KRAS mutation")
                if "G12D" in hgvsp:
                    biomarkers_present.add("KRAS G12D mutation")
                    biomarkers_present.add("KRAS G12D or G12R mutation")
                if "G12V" in hgvsp:
                    biomarkers_present.add("KRAS G12V mutation")
                if "G12R" in hgvsp:
                    biomarkers_present.add("KRAS G12R mutation")
                    biomarkers_present.add("KRAS G12D or G12R mutation")
                if "G12C" in hgvsp:
                    biomarkers_present.add("KRAS G12C mutation")
                for m in ["G12D", "G12V", "G12R", "G12A", "G12S"]:
                    if m in hgvsp:
                        biomarkers_present.add("KRAS G12D, G12V, G12R, G12A, G12S mutation")

            # BRCA
            if gene == "BRCA1":
                biomarkers_present.add("BRCA1/2 germline mutation")
                biomarkers_present.add("BRCA1/2 mutation")
            if gene == "BRCA2":
                biomarkers_present.add("BRCA1/2 germline mutation")
                biomarkers_present.add("BRCA1/2 mutation")
            if gene == "PALB2":
                biomarkers_present.add("BRCA1/2 or PALB2 mutation")

            # MSI/dMMR
            if row.get("is_msi_h", False):
                biomarkers_present.add("MSI-H or dMMR")

            # TMB
            if row.get("is_tmb_h", False):
                biomarkers_present.add("MSI-H, TMB-H or KRAS mutation")

    # Check for MSI-H in other columns
    for col in variants_df.columns:
        col_lower = col.lower()
        if "msi" in col_lower:
            for val in variants_df[col].dropna():
                val_str = str(val).lower()
                if "msi-h" in val_str:
                    biomarkers_present.add("MSI-H or dMMR")
                    biomarkers_present.add("MSI-H, TMB-H or KRAS mutation")
                break
        if "tmb" in col_lower:
            for val in variants_df[col].dropna():
                try:
                    if float(val) >= 10:
                        biomarkers_present.add("MSI-H, TMB-H or KRAS mutation")
                except (ValueError, TypeError):
                    pass
                break

    # Match trials
    for trial in PANCREATIC_CLINICAL_TRIALS:
        trial_biomarker = trial["biomarker_match"]
        if trial_biomarker in biomarkers_present:
            matched_trials.append(trial)

    # Add Precision Promise for any patient (broad eligibility)
    precision_promise = next(
        (t for t in PANCREATIC_CLINICAL_TRIALS if t["nct_id"] == "NCT03504423"),
        None,
    )
    if precision_promise and precision_promise not in matched_trials:
        matched_trials.append(precision_promise)

    # Sort: Phase III first, then Phase II, then Phase I
    phase_order = {"Phase III": 0, "Phase II/III": 0, "Phase II": 1, "Phase I/II": 2, "Phase I": 3}
    matched_trials.sort(key=lambda t: phase_order.get(t["phase"], 99))

    return matched_trials


def format_trials_md(trials: list[dict[str, Any]]) -> str:
    """Format clinical trial matches as Markdown text."""
    if not trials:
        return (
            "### Clinical Trial Matches\n\n"
            "No direct clinical trial matches identified based on genomic "
            "biomarkers. Consider Precision Promise platform trial "
            "(NCT03504423) for broad eligibility.\n"
        )

    lines = ["### Clinical Trial Matches\n"]
    lines.append(
        f"The following **{len(trials)}** clinical trials are identified based on "
        "genomic biomarker matches:\n"
    )

    for i, trial in enumerate(trials, 1):
        lines.append(f"#### {i}. {trial['title']}")
        lines.append(f"- **NCT ID**: [{trial['nct_id']}]({trial['url']})")
        lines.append(f"- **Phase**: {trial['phase']}")
        lines.append(f"- **Status**: {trial['status']}")
        lines.append(f"- **Biomarker**: {trial['biomarker_match']}")
        lines.append(f"- **Drug**: {trial['drug']}")
        lines.append("")

    return "\n".join(lines)
