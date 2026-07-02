"""Clinical trials matching endpoints — backed by ClinicalTrials.gov API v2.

Falls back to a curated local database when the API is unavailable.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database.models import CancerPatient, SomaticVariant
from backend.database.session import get_db
from backend.services.clinicaltrials_client import ClinicalTrialsClient

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class TrialMatch(BaseModel):
    nct_id: str
    title: str
    phase: str
    status: str
    conditions: str
    interventions: str
    match_reason: str
    url: str


class TrialMatchResponse(BaseModel):
    patient_id: int
    matched_genes: list[str]
    total_trials: int
    trials: list[TrialMatch]


# ---------------------------------------------------------------------------
# Fallback: curated local trial database (used when API is unavailable)
# ---------------------------------------------------------------------------

_FALLBACK_TRIALS: list[dict[str, str]] = [
    {
        "nct_id": "NCT03504423",
        "title": "Olaparib as Adjuvant Treatment in Patients With Germline BRCA Mutated Pancreatic Cancer (POLO)",
        "phase": "Phase III",
        "status": "Active, not recruiting",
        "conditions": "Pancreatic Cancer | BRCA1 Mutation | BRCA2 Mutation",
        "interventions": "Olaparib (PARP inhibitor)",
        "genes": "BRCA1,BRCA2",
    },
    {
        "nct_id": "NCT03600883",
        "title": "A Study of Sotorasib in KRAS G12C Mutant Pancreatic Cancer",
        "phase": "Phase II",
        "status": "Recruiting",
        "conditions": "Pancreatic Cancer | KRAS G12C",
        "interventions": "Sotorasib (AMG 510)",
        "genes": "KRAS",
    },
    {
        "nct_id": "NCT04449874",
        "title": "Pembrolizumab in MSI-H/dMMR Pancreatic Cancer",
        "phase": "Phase II",
        "status": "Recruiting",
        "conditions": "Pancreatic Cancer | MSI-H",
        "interventions": "Pembrolizumab (anti-PD1)",
        "genes": "MSI-H",
    },
    {
        "nct_id": "NCT03040999",
        "title": "Niraparib in Patients With Pancreatic Cancer (NIRA-PANC)",
        "phase": "Phase II",
        "status": "Active, not recruiting",
        "conditions": "Pancreatic Cancer | BRCA Mutation",
        "interventions": "Niraparib (PARP inhibitor)",
        "genes": "BRCA1,BRCA2",
    },
    {
        "nct_id": "NCT02538627",
        "title": "Entrectinib in NTRK Fusion-Positive Solid Tumors",
        "phase": "Phase II",
        "status": "Recruiting",
        "conditions": "Solid Tumors | NTRK Fusion | Pancreatic Cancer",
        "interventions": "Entrectinib (TRK inhibitor)",
        "genes": "NTRK1,NTRK2,NTRK3",
    },
    {
        "nct_id": "NCT03682289",
        "title": "APR-246 in Combination With Chemotherapy in TP53 Mutant Cancer",
        "phase": "Phase I/II",
        "status": "Recruiting",
        "conditions": "TP53 Mutant Cancer | Pancreatic Cancer",
        "interventions": "APR-246 + Chemotherapy",
        "genes": "TP53",
    },
    {
        "nct_id": "NCT01938612",
        "title": "Palbociclib in CDKN2A-Altered Pancreatic Cancer",
        "phase": "Phase II",
        "status": "Recruiting",
        "conditions": "Pancreatic Cancer | CDKN2A Alteration",
        "interventions": "Palbociclib (CDK4/6 inhibitor)",
        "genes": "CDKN2A",
    },
    {
        "nct_id": "NCT04132973",
        "title": "Galunisertib + Durvalumab in Metastatic Pancreatic Cancer",
        "phase": "Phase I/II",
        "status": "Recruiting",
        "conditions": "Pancreatic Cancer | SMAD4 Mutation",
        "interventions": "Galunisertib + Durvalumab",
        "genes": "SMAD4",
    },
    {
        "nct_id": "NCT04383210",
        "title": "Adagrasib in KRAS G12C Mutant Advanced Solid Tumors",
        "phase": "Phase II",
        "status": "Recruiting",
        "conditions": "Pancreatic Cancer | KRAS G12C",
        "interventions": "Adagrasib (MRTX849)",
        "genes": "KRAS",
    },
    {
        "nct_id": "NCT04267939",
        "title": "Alpelisib + FOLFOX in PIK3CA Mutant Pancreatic Cancer",
        "phase": "Phase I/II",
        "status": "Recruiting",
        "conditions": "Pancreatic Cancer | PIK3CA Mutation",
        "interventions": "Alpelisib + FOLFOX",
        "genes": "PIK3CA",
    },
    {
        "nct_id": "NCT03829436",
        "title": "Zenocutuzumab in NRG1 Fusion-Positive Pancreatic Cancer",
        "phase": "Phase II",
        "status": "Recruiting",
        "conditions": "Pancreatic Cancer | NRG1 Fusion",
        "interventions": "Zenocutuzumab (MCLA-128)",
        "genes": "NRG1",
    },
    {
        "nct_id": "NCT04548752",
        "title": "Rucaparib in BRCA/PALB2 Mutated Pancreatic Cancer",
        "phase": "Phase II",
        "status": "Recruiting",
        "conditions": "Pancreatic Cancer | BRCA1 | BRCA2 | PALB2",
        "interventions": "Rucaparib (PARP inhibitor)",
        "genes": "BRCA1,BRCA2,PALB2",
    },
    {
        "nct_id": "NCT04802889",
        "title": "Larotrectinib in TRK Fusion Pancreatic Cancer",
        "phase": "Phase II",
        "status": "Recruiting",
        "conditions": "Pancreatic Cancer | NTRK Fusion",
        "interventions": "Larotrectinib (TRK inhibitor)",
        "genes": "NTRK1,NTRK2,NTRK3",
    },
    {
        "nct_id": "NCT03982173",
        "title": "Trastuzumab Deruxtecan in HER2-Positive Pancreatic Cancer",
        "phase": "Phase II",
        "status": "Recruiting",
        "conditions": "Pancreatic Cancer | HER2 Positive",
        "interventions": "Trastuzumab Deruxtecan (T-DXd)",
        "genes": "HER2",
    },
    {
        "nct_id": "NCT03404960",
        "title": "Nivolumab + Ipilimumab in Pancreatic Cancer With Inherited Syndromes",
        "phase": "Phase II",
        "status": "Recruiting",
        "conditions": "Pancreatic Cancer | Lynch Syndrome | BRCA",
        "interventions": "Nivolumab + Ipilimumab",
        "genes": "BRCA1,BRCA2,MSI-H,MLH1,MSH2,MSH6,PMS2",
    },
]


# ---------------------------------------------------------------------------
# API-backed matching
# ---------------------------------------------------------------------------

async def _fetch_api_trials(gene: str | None = None) -> list[dict]:
    """Try to fetch trials from ClinicalTrials.gov API."""
    client = ClinicalTrialsClient()
    try:
        trials = await client.search_pancreatic_cancer_trials(gene=gene)
        return trials
    except Exception:
        logger.warning("ClinicalTrials.gov API unavailable, using fallback data")
        return []
    finally:
        await client.aclose()


def _match_fallback_trials(variant_genes: list[str]) -> list[TrialMatch]:
    """Match against the curated fallback trial database."""
    matched: list[TrialMatch] = []
    for trial in _FALLBACK_TRIALS:
        trial_genes = [g.strip() for g in trial["genes"].split(",")]
        hit = [g for g in variant_genes if g in trial_genes]
        if hit:
            matched.append(TrialMatch(
                nct_id=trial["nct_id"],
                title=trial["title"],
                phase=trial["phase"],
                status=trial["status"],
                conditions=trial["conditions"],
                interventions=trial["interventions"],
                match_reason=f"Gene match: {', '.join(hit)}",
                url=f"https://clinicaltrials.gov/study/{trial['nct_id']}",
            ))
    return matched


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/match/{patient_id}", response_model=TrialMatchResponse, tags=["trials"])
async def match_trials(
    patient_id: int,
    use_api: bool = Query(default=True, description="Use ClinicalTrials.gov API (fallback to local if unavailable)"),
    limit: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> TrialMatchResponse:
    """Find clinical trials matching the patient's variant profile."""
    # Verify patient exists
    result = await db.execute(
        select(CancerPatient).where(CancerPatient.id == patient_id)
    )
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient not found: {patient_id}")

    # Get somatic variant genes
    var_result = await db.execute(
        select(SomaticVariant).where(SomaticVariant.patient_id == patient_id)
    )
    somatic_variants = var_result.scalars().all()
    variant_genes = list({v.gene for v in somatic_variants if v.gene})

    # Check biomarkers for MSI-H status
    if patient.biomarkers:
        if patient.biomarkers.get("MSI") == "MSI-H":
            if "MSI-H" not in variant_genes:
                variant_genes.append("MSI-H")

    matched_trials: list[TrialMatch] = []

    # Try API first
    if use_api and variant_genes:
        for gene in variant_genes:
            api_trials = await _fetch_api_trials(gene=gene)
            for t in api_trials:
                # Deduplicate by nct_id
                if not any(m.nct_id == t["nct_id"] for m in matched_trials):
                    matched_trials.append(TrialMatch(
                        nct_id=t["nct_id"],
                        title=t["title"],
                        phase=t.get("phase", ""),
                        status=t.get("status", ""),
                        conditions=t.get("conditions", ""),
                        interventions=t.get("interventions", ""),
                        match_reason=t.get("biomarker_match", f"Gene: {gene}"),
                        url=t.get("url", f"https://clinicaltrials.gov/study/{t['nct_id']}"),
                    ))

    # Fallback to local database if API returned nothing
    if not matched_trials:
        matched_trials = _match_fallback_trials(variant_genes)

    # General pancreatic cancer trial if no matches
    if not matched_trials:
        matched_trials.append(TrialMatch(
            nct_id="NCT04166721",
            title="Master Protocol for Pancreatic Cancer Precision Medicine",
            phase="Phase II",
            status="Recruiting",
            conditions="Pancreatic Cancer",
            interventions="Multiple targeted therapies based on genomic profiling",
            match_reason="General pancreatic cancer precision medicine trial",
            url="https://clinicaltrials.gov/study/NCT04166721",
        ))

    return TrialMatchResponse(
        patient_id=patient_id,
        matched_genes=variant_genes,
        total_trials=len(matched_trials),
        trials=matched_trials[:limit],
    )


@router.get("/search", response_model=list[TrialMatch], tags=["trials"])
async def search_trials(
    gene: str = Query(..., description="Gene symbol to search for"),
    use_api: bool = Query(default=True, description="Use ClinicalTrials.gov API"),
    limit: int = Query(default=20, ge=1, le=50),
) -> list[TrialMatch]:
    """Search clinical trials by gene."""
    matched: list[TrialMatch] = []

    # Try API first
    if use_api:
        api_trials = await _fetch_api_trials(gene=gene)
        for t in api_trials:
            matched.append(TrialMatch(
                nct_id=t["nct_id"],
                title=t["title"],
                phase=t.get("phase", ""),
                status=t.get("status", ""),
                conditions=t.get("conditions", ""),
                interventions=t.get("interventions", ""),
                match_reason=t.get("biomarker_match", f"Gene: {gene}"),
                url=t.get("url", f"https://clinicaltrials.gov/study/{t['nct_id']}"),
            ))

    # Fallback to local
    if not matched:
        gene_upper = gene.upper()
        for trial in _FALLBACK_TRIALS:
            trial_genes = [g.strip().upper() for g in trial["genes"].split(",")]
            if gene_upper in trial_genes:
                matched.append(TrialMatch(
                    nct_id=trial["nct_id"],
                    title=trial["title"],
                    phase=trial["phase"],
                    status=trial["status"],
                    conditions=trial["conditions"],
                    interventions=trial["interventions"],
                    match_reason=f"Gene match: {gene}",
                    url=f"https://clinicaltrials.gov/study/{trial['nct_id']}",
                ))

    return matched[:limit]
