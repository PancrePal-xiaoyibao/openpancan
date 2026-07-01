"""Clinical trials matching endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database.models import CancerPatient, SomaticVariant
from backend.database.session import get_db

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
# Reference trial data (would normally come from ClinicalTrials.gov API)
# ---------------------------------------------------------------------------

_PANCREATIC_CANCER_TRIALS: list[dict[str, str]] = [
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
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/match/{patient_id}", response_model=TrialMatchResponse, tags=["trials"])
async def match_trials(
    patient_id: int,
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

    # Match trials
    matched_trials: list[TrialMatch] = []
    for trial in _PANCREATIC_CANCER_TRIALS:
        trial_genes = [g.strip() for g in trial["genes"].split(",")]
        matched_genes = [g for g in variant_genes if g in trial_genes]

        if matched_genes:
            matched_trials.append(TrialMatch(
                nct_id=trial["nct_id"],
                title=trial["title"],
                phase=trial["phase"],
                status=trial["status"],
                conditions=trial["conditions"],
                interventions=trial["interventions"],
                match_reason=f"Gene match: {', '.join(matched_genes)}",
                url=f"https://clinicaltrials.gov/study/{trial['nct_id']}",
            ))

    # Add general pancreatic cancer trials even without gene match
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
    limit: int = Query(default=20, ge=1, le=50),
) -> list[TrialMatch]:
    """Search clinical trials by gene."""
    matched: list[TrialMatch] = []
    gene_upper = gene.upper()

    for trial in _PANCREATIC_CANCER_TRIALS:
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
