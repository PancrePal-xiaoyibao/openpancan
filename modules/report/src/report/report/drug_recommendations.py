"""
Pancreatic cancer drug recommendations.

Provides evidence-based drug recommendation logic for pancreatic
ductal adenocarcinoma based on genomic biomarkers, including:
- KRAS mutations (G12C, pan-KRAS)
- BRCA1/2, PALB2 (PARP inhibitors)
- MSI-H / dMMR (immunotherapy)
- NTRK fusions (TRK inhibitors)
- HER2 amplification (HER2-targeted)
- TMB-H (immunotherapy)
- BRAF V600E (BRAF+MEK inhibitors)
- PIK3CA (PI3K inhibitors)
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Drug recommendation database (pancreatic cancer focused)
# ---------------------------------------------------------------------------
DRUG_RECOMMENDATIONS: list[dict[str, Any]] = [
    # ---- KRAS-targeted ----
    {
        "drug": "Sotorasib (AMG 510)",
        "target": "KRAS G12C",
        "biomarker": "KRAS G12C mutation",
        "evidence_level": "FDA-approved (NSCLC, off-label in pancreatic)",
        "source": "CodeBreaK 100, KRYSTAL-1",
        "description": (
            "KRAS G12C inhibitor. FDA-approved for KRAS G12C-mutant NSCLC. "
            "Phase I/II data in pancreatic cancer showed ~21% response rate. "
            "Consider for patients with KRAS G12C-mutant pancreatic cancer "
            "who have progressed on standard therapy."
        ),
    },
    {
        "drug": "Adagrasib (MRTX849)",
        "target": "KRAS G12C",
        "biomarker": "KRAS G12C mutation",
        "evidence_level": "FDA-approved (NSCLC, off-label in pancreatic)",
        "source": "KRYSTAL-1",
        "description": (
            "KRAS G12C inhibitor with CNS penetration. Phase II data in "
            "pancreatic cancer showed ~33% response rate. May be considered "
            "as an alternative to sotorasib for KRAS G12C-mutant pancreatic cancer."
        ),
    },
    {
        "drug": "RMC-6236",
        "target": "Pan-KRAS (G12D/V/R)",
        "biomarker": "KRAS G12D, G12V, G12R mutation",
        "evidence_level": "Phase I clinical trial",
        "source": "NCT05379985",
        "description": (
            "Pan-RAS molecular glue (RAS(ON) multi-selective tri-complex inhibitor). "
            "Covers KRAS G12D, G12V, G12R and other common KRAS mutations. "
            "Early clinical data shows promising activity in pancreatic cancer "
            "with common KRAS mutations."
        ),
    },
    {
        "drug": "MRTX1133",
        "target": "KRAS G12D",
        "biomarker": "KRAS G12D mutation",
        "evidence_level": "Phase I/II clinical trial",
        "source": "NCT05737706",
        "description": (
            "Selective KRAS G12D inhibitor. KRAS G12D is the most common "
            "KRAS mutation in pancreatic cancer (~36% of cases). Phase I data "
            "shows preliminary efficacy in KRAS G12D-mutant solid tumors."
        ),
    },
    # ---- PARP inhibitors (BRCA1/2, PALB2) ----
    {
        "drug": "Olaparib (Lynparza)",
        "target": "PARP1/2",
        "biomarker": "BRCA1/2 germline mutation",
        "evidence_level": "FDA-approved (maintenance, POLO trial)",
        "source": "POLO (NCT02184195)",
        "description": (
            "PARP inhibitor. FDA-approved as maintenance therapy for germline "
            "BRCA-mutated metastatic pancreatic adenocarcinoma that has not "
            "progressed on ≥16 weeks of first-line platinum-based chemotherapy. "
            "POLO trial showed PFS benefit (7.4 vs 3.8 months)."
        ),
    },
    {
        "drug": "Rucaparib (Rubraca)",
        "target": "PARP1/2/3",
        "biomarker": "BRCA1/2 mutation",
        "evidence_level": "Phase II/III (NCCN 2A for pancreatic)",
        "source": "NCT03140670",
        "description": (
            "PARP inhibitor with activity in BRCA1/2-mutated pancreatic cancer. "
            "May be considered as an alternative to olaparib for maintenance "
            "therapy or in the treatment setting."
        ),
    },
    {
        "drug": "Niraparib (Zejula)",
        "target": "PARP1/2",
        "biomarker": "BRCA1/2, PALB2 mutation",
        "evidence_level": "Phase II (NCCN 2A for pancreatic)",
        "source": "NCT03553004",
        "description": (
            "PARP inhibitor. Consider for BRCA1/2 or PALB2-mutated pancreatic "
            "cancer. May be used as maintenance therapy or in platinum-sensitive "
            "disease."
        ),
    },
    # ---- Immunotherapy (MSI-H / dMMR) ----
    {
        "drug": "Pembrolizumab (Keytruda)",
        "target": "PD-1",
        "biomarker": "MSI-H or dMMR",
        "evidence_level": "FDA-approved (tumor-agnostic)",
        "source": "KEYNOTE-158, KEYNOTE-164",
        "description": (
            "Anti-PD-1 immunotherapy. FDA-approved for MSI-H/dMMR solid tumors "
            "regardless of origin. In pancreatic cancer patients with MSI-H/dMMR, "
            "response rates of ~18-30% have been reported. Consider especially "
            "in Lynch syndrome-associated pancreatic cancer."
        ),
    },
    {
        "drug": "Dostarlimab (Jemperli)",
        "target": "PD-1",
        "biomarker": "dMMR/MSI-H",
        "evidence_level": "FDA-approved (tumor-agnostic, dMMR)",
        "source": "GARNET trial",
        "description": (
            "Anti-PD-1 immunotherapy. FDA-approved for dMMR recurrent or "
            "advanced solid tumors. Alternative to pembrolizumab for "
            "MSI-H/dMMR pancreatic cancer."
        ),
    },
    # ---- NTRK fusions ----
    {
        "drug": "Larotrectinib (Vitrakvi)",
        "target": "TRK A/B/C",
        "biomarker": "NTRK1/2/3 gene fusion",
        "evidence_level": "FDA-approved (tumor-agnostic)",
        "source": "LOXO-TRK-14001, NAVIGATE",
        "description": (
            "First-generation TRK inhibitor. FDA-approved for NTRK fusion-positive "
            "solid tumors. NTRK fusions are rare in pancreatic cancer (<1%) but "
            "when present, larotrectinib shows high response rates (>75%)."
        ),
    },
    {
        "drug": "Entrectinib (Rozlytrek)",
        "target": "TRK A/B/C, ROS1, ALK",
        "biomarker": "NTRK1/2/3 gene fusion",
        "evidence_level": "FDA-approved (tumor-agnostic)",
        "source": "STARTRK-2",
        "description": (
            "Multi-kinase inhibitor with CNS penetration. FDA-approved for "
            "NTRK fusion-positive solid tumors. Consider if CNS metastases "
            "are present in NTRK-fusion pancreatic cancer."
        ),
    },
    # ---- BRAF V600E ----
    {
        "drug": "Dabrafenib + Trametinib",
        "target": "BRAF V600E + MEK",
        "biomarker": "BRAF V600E mutation",
        "evidence_level": "FDA-approved (tumor-agnostic)",
        "source": "ROAR basket trial, NCI-MATCH",
        "description": (
            "BRAF inhibitor + MEK inhibitor combination. FDA-approved for "
            "BRAF V600E-mutant solid tumors. In pancreatic cancer, the ROAR "
            "basket trial showed limited but meaningful activity. Consider "
            "in BRAF V600E-mutant pancreatic cancer after standard therapy."
        ),
    },
    # ---- HER2 ----
    {
        "drug": "Trastuzumab Deruxtecan (Enhertu)",
        "target": "HER2 (ERBB2)",
        "biomarker": "HER2 amplification or mutation",
        "evidence_level": "FDA-approved (tumor-agnostic, HER2+ IHC3+)",
        "source": "DESTINY-PanTumor02",
        "description": (
            "Antibody-drug conjugate targeting HER2. FDA-approved for HER2-positive "
            "(IHC 3+) solid tumors. The DESTINY-PanTumor02 trial included "
            "pancreatic cancer patients and showed responses in HER2-expressing tumors."
        ),
    },
    # ---- TMB-H immunotherapy ----
    {
        "drug": "Pembrolizumab (Keytruda) – TMB-H",
        "target": "PD-1",
        "biomarker": "TMB ≥10 mut/Mb",
        "evidence_level": "FDA-approved (tumor-agnostic, TMB-H)",
        "source": "KEYNOTE-158",
        "description": (
            "Anti-PD-1 immunotherapy for TMB-H (≥10 mut/Mb) solid tumors. "
            "In pancreatic cancer, TMB-H is rare (~1-2%) but patients with "
            "TMB-H may benefit from pembrolizumab."
        ),
    },
    # ---- Standard chemotherapy agents (for reference) ----
    {
        "drug": "FOLFIRINOX",
        "target": "Multiple (5-FU, irinotecan, oxaliplatin)",
        "biomarker": "None required (standard of care)",
        "evidence_level": "Standard first-line (PRODIGE 4/ACCORD 11)",
        "source": "PRODIGE 4/ACCORD 11, NAPOLI-3",
        "description": (
            "Combination chemotherapy: 5-FU, leucovorin, irinotecan, oxaliplatin. "
            "Standard first-line regimen for metastatic pancreatic cancer in "
            "patients with good performance status (ECOG 0-1). PRODIGE 4 trial "
            "showed median OS of 11.1 months vs 6.8 months for gemcitabine."
        ),
    },
    {
        "drug": "Gemcitabine + nab-Paclitaxel",
        "target": "DNA synthesis + microtubules",
        "biomarker": "None required (standard of care)",
        "evidence_level": "Standard first-line (MPACT trial)",
        "source": "MPACT (NCT00844649)",
        "description": (
            "Gemcitabine plus nab-paclitaxel. Standard first-line option for "
            "metastatic pancreatic cancer. MPACT trial showed median OS of "
            "8.5 months vs 6.7 months for gemcitabine alone. Consider if "
            "FOLFIRINOX is not tolerated."
        ),
    },
    {
        "drug": "Nanoliposomal Irinotecan (nal-IRI) + 5-FU/LV",
        "target": "Topoisomerase I",
        "biomarker": "None required (second-line)",
        "evidence_level": "Standard second-line (NAPOLI-1)",
        "source": "NAPOLI-1, NAPOLI-3",
        "description": (
            "Nanoliposomal irinotecan with 5-FU/leucovorin. Standard "
            "second-line therapy after gemcitabine-based progression. "
            "NAPOLI-1 trial showed median OS of 6.1 months vs 4.2 months "
            "for 5-FU/LV alone."
        ),
    },
]


def get_drug_recommendations(
    variants_df: pd.DataFrame,
    cancer_type: str = "pancreatic_ductal_adenocarcinoma",
) -> list[dict[str, Any]]:
    """
    Generate drug recommendations based on genomic variants.

    Parameters
    ----------
    variants_df : pd.DataFrame
        DataFrame of variants with SYMBOL, HGVSp, and biomarker columns.
    cancer_type : str
        Cancer type for contextual recommendations.

    Returns
    -------
    list[dict]
        Recommended drugs with evidence levels.
    """
    recommendations: list[dict[str, Any]] = []
    seen_drugs: set[str] = set()

    # Collect biomarkers from variants
    biomarkers_found: set[str] = set()

    if "SYMBOL" in variants_df.columns:
        for _, row in variants_df.iterrows():
            gene = str(row.get("SYMBOL", ""))
            hgvsp = str(row.get("HGVSp", ""))

            # KRAS mutations
            if gene == "KRAS":
                if "G12C" in hgvsp:
                    biomarkers_found.add("KRAS G12C mutation")
                elif "G12D" in hgvsp:
                    biomarkers_found.add("KRAS G12D mutation")
                elif "G12V" in hgvsp:
                    biomarkers_found.add("KRAS G12V mutation")
                elif "G12R" in hgvsp:
                    biomarkers_found.add("KRAS G12R mutation")
                elif any(m in hgvsp for m in ["G12", "G13", "Q61"]):
                    biomarkers_found.add("KRAS mutation (other)")

            # BRCA
            if gene in ("BRCA1", "BRCA2") and "is_cancer_hotspot" in variants_df.columns:
                biomarkers_found.add("BRCA1/2 germline mutation")
            elif gene in ("BRCA1", "BRCA2"):
                biomarkers_found.add("BRCA1/2 germline mutation")

            # PALB2
            if gene == "PALB2":
                biomarkers_found.add("BRCA1/2, PALB2 mutation")

            # BRAF
            if gene == "BRAF" and "V600" in hgvsp:
                biomarkers_found.add("BRAF V600E mutation")

            # HER2
            if gene == "ERBB2" or (gene == "HER2"):
                biomarkers_found.add("HER2 amplification or mutation")

            # NTRK
            if gene in ("NTRK1", "NTRK2", "NTRK3"):
                biomarkers_found.add("NTRK1/2/3 gene fusion")

            # PIK3CA
            if gene == "PIK3CA":
                biomarkers_found.add("PIK3CA mutation")

    # Check additional biomarker columns
    for col in variants_df.columns:
        col_lower = col.lower()
        if "msi" in col_lower or "dmmr" in col_lower:
            for val in variants_df[col].dropna():
                val_str = str(val).lower()
                if "msi-h" in val_str or "high" in val_str:
                    biomarkers_found.add("MSI-H or dMMR")
                break
        if "tmb" in col_lower:
            for val in variants_df[col].dropna():
                try:
                    tmb_val = float(val)
                    if tmb_val >= 10:
                        biomarkers_found.add("TMB ≥10 mut/Mb")
                except (ValueError, TypeError):
                    pass
                break

    # Match drugs to biomarkers
    for drug in DRUG_RECOMMENDATIONS:
        if drug["biomarker"] in biomarkers_found and drug["drug"] not in seen_drugs:
            recommendations.append(drug)
            seen_drugs.add(drug["drug"])

    # Always include standard-of-care info
    soc_drugs = ["FOLFIRINOX", "Gemcitabine + nab-Paclitaxel"]
    for drug in DRUG_RECOMMENDATIONS:
        if drug["drug"] in soc_drugs and drug["drug"] not in seen_drugs:
            recommendations.append(drug)
            seen_drugs.add(drug["drug"])

    return recommendations


def format_drug_recommendations_md(
    recommendations: list[dict[str, Any]],
) -> str:
    """Format drug recommendations as Markdown text."""
    if not recommendations:
        return "### Drug Recommendations\n\nNo targeted therapy recommendations based on genomic findings.\n\nStandard chemotherapy options (FOLFIRINOX, Gemcitabine/nab-Paclitaxel) remain the standard of care.\n"

    lines = ["### Drug Recommendations\n"]
    lines.append("The following therapeutic options are identified based on genomic biomarkers:\n")

    for i, rec in enumerate(recommendations, 1):
        lines.append(f"#### {i}. {rec['drug']}")
        lines.append(f"- **Target**: {rec['target']}")
        lines.append(f"- **Biomarker**: {rec['biomarker']}")
        lines.append(f"- **Evidence Level**: {rec['evidence_level']}")
        lines.append(f"- **Source**: {rec['source']}")
        lines.append(f"- **Rationale**: {rec['description']}")
        lines.append("")

    return "\n".join(lines)
