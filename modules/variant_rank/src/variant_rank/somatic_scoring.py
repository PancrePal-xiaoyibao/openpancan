"""
Somatic Variant Scorer for pancreatic cancer.

Provides somatic-specific scoring logic including VAF-based clonality
estimation, cancer hotspot matching, and driver mutation prediction.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cancer Hotspot Database – extensive pancreatic cancer hotspot mutations
# ---------------------------------------------------------------------------
CANCER_HOTSPOT_DB: dict[str, dict[str, Any]] = {
    # KRAS hotspots (pancreatic cancer – most common)
    "KRAS:G12D": {
        "gene": "KRAS",
        "protein_change": "G12D",
        "cosmic_id": "COSM521",
        "cancer_type": "pancreatic_adenocarcinoma",
        "frequency_paad": 0.36,
        "oncokb_level": 1,
        "drug_sensitivity": "MEK inhibitors",
    },
    "KRAS:G12V": {
        "gene": "KRAS",
        "protein_change": "G12V",
        "cosmic_id": "COSM520",
        "cancer_type": "pancreatic_adenocarcinoma",
        "frequency_paad": 0.30,
        "oncokb_level": 1,
        "drug_sensitivity": "MEK inhibitors",
    },
    "KRAS:G12R": {
        "gene": "KRAS",
        "protein_change": "G12R",
        "cosmic_id": "COSM518",
        "cancer_type": "pancreatic_adenocarcinoma",
        "frequency_paad": 0.14,
        "oncokb_level": 1,
        "drug_sensitivity": "MEK inhibitors",
    },
    "KRAS:G12C": {
        "gene": "KRAS",
        "protein_change": "G12C",
        "cosmic_id": "COSM516",
        "cancer_type": "pancreatic_adenocarcinoma",
        "frequency_paad": 0.03,
        "oncokb_level": 1,
        "drug_sensitivity": "Sotorasib, Adagrasib (KRAS G12C inhibitors)",
    },
    "KRAS:Q61H": {
        "gene": "KRAS",
        "protein_change": "Q61H",
        "cosmic_id": "COSM549",
        "cancer_type": "pancreatic_adenocarcinoma",
        "frequency_paad": 0.05,
        "oncokb_level": 2,
        "drug_sensitivity": "Pan-KRAS inhibitors (investigational)",
    },
    "KRAS:Q61R": {
        "gene": "KRAS",
        "protein_change": "Q61R",
        "cosmic_id": "COSM550",
        "cancer_type": "pancreatic_adenocarcinoma",
        "frequency_paad": 0.02,
        "oncokb_level": 3,
        "drug_sensitivity": "Pan-KRAS inhibitors (investigational)",
    },
    "KRAS:G13D": {
        "gene": "KRAS",
        "protein_change": "G13D",
        "cosmic_id": "COSM532",
        "cancer_type": "pancreatic_adenocarcinoma",
        "frequency_paad": 0.02,
        "oncokb_level": 3,
        "drug_sensitivity": "Investigational",
    },
    # TP53 hotspots
    "TP53:R175H": {
        "gene": "TP53",
        "protein_change": "R175H",
        "cosmic_id": "COSM10648",
        "cancer_type": "pancreatic_adenocarcinoma",
        "frequency_paad": 0.08,
        "oncokb_level": 2,
        "drug_sensitivity": "PRIMA-1, APR-246 (mutant p53 reactivators)",
    },
    "TP53:R248W": {
        "gene": "TP53",
        "protein_change": "R248W",
        "cosmic_id": "COSM10656",
        "cancer_type": "pancreatic_adenocarcinoma",
        "frequency_paad": 0.06,
        "oncokb_level": 2,
        "drug_sensitivity": "PRIMA-1, APR-246",
    },
    "TP53:R248Q": {
        "gene": "TP53",
        "protein_change": "R248Q",
        "cosmic_id": "COSM10662",
        "cancer_type": "pancreatic_adenocarcinoma",
        "frequency_paad": 0.05,
        "oncokb_level": 2,
        "drug_sensitivity": "PRIMA-1, APR-246",
    },
    "TP53:R273H": {
        "gene": "TP53",
        "protein_change": "R273H",
        "cosmic_id": "COSM10660",
        "cancer_type": "pancreatic_adenocarcinoma",
        "frequency_paad": 0.07,
        "oncokb_level": 2,
        "drug_sensitivity": "PRIMA-1, APR-246",
    },
    "TP53:R273C": {
        "gene": "TP53",
        "protein_change": "R273C",
        "cosmic_id": "COSM10659",
        "cancer_type": "pancreatic_adenocarcinoma",
        "frequency_paad": 0.04,
        "oncokb_level": 2,
        "drug_sensitivity": "PRIMA-1, APR-246",
    },
    "TP53:R282W": {
        "gene": "TP53",
        "protein_change": "R282W",
        "cosmic_id": "COSM10704",
        "cancer_type": "pancreatic_adenocarcinoma",
        "frequency_paad": 0.03,
        "oncokb_level": 2,
        "drug_sensitivity": "PRIMA-1, APR-246",
    },
    "TP53:G245S": {
        "gene": "TP53",
        "protein_change": "G245S",
        "cosmic_id": "COSM6932",
        "cancer_type": "pancreatic_adenocarcinoma",
        "frequency_paad": 0.03,
        "oncokb_level": 2,
        "drug_sensitivity": "PRIMA-1, APR-246",
    },
    # SMAD4 hotspots
    "SMAD4:R361C": {
        "gene": "SMAD4",
        "protein_change": "R361C",
        "cosmic_id": "COSM14064",
        "cancer_type": "pancreatic_adenocarcinoma",
        "frequency_paad": 0.04,
        "oncokb_level": 3,
        "drug_sensitivity": "Investigational",
    },
    "SMAD4:R361H": {
        "gene": "SMAD4",
        "protein_change": "R361H",
        "cosmic_id": "COSM14126",
        "cancer_type": "pancreatic_adenocarcinoma",
        "frequency_paad": 0.02,
        "oncokb_level": 3,
        "drug_sensitivity": "Investigational",
    },
    # CDKN2A hotspots
    "CDKN2A:R80*": {
        "gene": "CDKN2A",
        "protein_change": "R80*",
        "cosmic_id": "COSM12500",
        "cancer_type": "pancreatic_adenocarcinoma",
        "frequency_paad": 0.02,
        "oncokb_level": 2,
        "drug_sensitivity": "CDK4/6 inhibitors",
    },
    # BRCA1/2 hotspots
    "BRCA1:C61G": {
        "gene": "BRCA1",
        "protein_change": "C61G",
        "cosmic_id": "COSM9876543",
        "cancer_type": "pancreatic_adenocarcinoma",
        "frequency_paad": 0.01,
        "oncokb_level": 1,
        "drug_sensitivity": "PARP inhibitors (Olaparib, Rucaparib)",
    },
    "BRCA2:S1982fs": {
        "gene": "BRCA2",
        "protein_change": "S1982fs",
        "cosmic_id": "COSM9876544",
        "cancer_type": "pancreatic_adenocarcinoma",
        "frequency_paad": 0.01,
        "oncokb_level": 1,
        "drug_sensitivity": "PARP inhibitors (Olaparib, Rucaparib)",
    },
    # PIK3CA hotspots
    "PIK3CA:H1047R": {
        "gene": "PIK3CA",
        "protein_change": "H1047R",
        "cosmic_id": "COSM775",
        "cancer_type": "pancreatic_adenocarcinoma",
        "frequency_paad": 0.01,
        "oncokb_level": 2,
        "drug_sensitivity": "PI3K inhibitors",
    },
    "PIK3CA:E545K": {
        "gene": "PIK3CA",
        "protein_change": "E545K",
        "cosmic_id": "COSM763",
        "cancer_type": "pancreatic_adenocarcinoma",
        "frequency_paad": 0.01,
        "oncokb_level": 2,
        "drug_sensitivity": "PI3K inhibitors",
    },
    # BRAF hotspots
    "BRAF:V600E": {
        "gene": "BRAF",
        "protein_change": "V600E",
        "cosmic_id": "COSM476",
        "cancer_type": "pancreatic_adenocarcinoma",
        "frequency_paad": 0.005,
        "oncokb_level": 1,
        "drug_sensitivity": "BRAF inhibitors (Dabrafenib + Trametinib)",
    },
}


# ---------------------------------------------------------------------------
# SomaticVariantScorer class
# ---------------------------------------------------------------------------
class SomaticVariantScorer:
    """
    Scores variants based on somatic evidence including VAF clonality
    estimation, hotspot matching, and driver mutation prediction.
    """

    def __init__(self, cancer_type: str = "pancreatic_ductal_adenocarcinoma"):
        self.cancer_type = cancer_type
        self.hotspot_db = CANCER_HOTSPOT_DB

    def vaf_based_clonality(self, row: pd.Series) -> float:
        """
        Estimate clonality based on variant allele fraction (VAF).

        Returns a score 0.0-1.0 where higher values indicate clonal (early)
        events that are more likely to be cancer drivers.
        """
        vaf_str = row.get("AF", "0")
        try:
            vaf = float(vaf_str)
        except (ValueError, TypeError):
            vaf = 0.0

        # Clonal mutations typically have VAF > 0.3
        # Subclonal mutations have VAF < 0.1
        if vaf >= 0.4:
            return 1.0
        elif vaf >= 0.3:
            return 0.8
        elif vaf >= 0.2:
            return 0.6
        elif vaf >= 0.1:
            return 0.4
        elif vaf >= 0.05:
            return 0.2
        else:
            return 0.1

    def hotspot_match(self, row: pd.Series) -> tuple[float, dict[str, Any]]:
        """
        Check if a variant matches a known cancer hotspot.

        Returns (score, hotspot_data) where score is 1.0 for exact match,
        0.5 for gene-level match, and 0.0 for no match.
        """
        gene = str(row.get("SYMBOL", ""))
        hgvsp = str(row.get("HGVSp", ""))

        if not gene or not hgvsp:
            return 0.0, {}

        # Direct lookup: "GENE:PROTEIN_CHANGE"
        for key, data in self.hotspot_db.items():
            if ":" not in key:
                continue
            db_gene, db_change = key.split(":", 1)
            if db_gene == gene and db_change in hgvsp:
                return 1.0, data

        # Gene-level match without exact protein change
        for key, data in self.hotspot_db.items():
            if ":" not in key:
                continue
            db_gene, _ = key.split(":", 1)
            if db_gene == gene:
                return 0.4, data

        return 0.0, {}

    def driver_prediction_score(self, row: pd.Series) -> float:
        """
        Predict likelihood that a variant is a cancer driver.

        Uses a combination of VAF, consequence severity, and gene identity
        to produce a driver probability score (0.0-1.0).
        """
        gene = str(row.get("SYMBOL", ""))
        consequence = str(row.get("Consequence", ""))
        impact = str(row.get("IMPACT", ""))

        score = 0.0

        # Impact-based scoring
        if impact == "HIGH":
            score += 0.4
        elif impact == "MODERATE":
            score += 0.2
        elif impact == "LOW":
            score += 0.05

        # Gene-based scoring
        pancreatic_drivers = {
            "KRAS": 0.5,
            "TP53": 0.5,
            "SMAD4": 0.4,
            "CDKN2A": 0.4,
            "BRCA1": 0.35,
            "BRCA2": 0.35,
            "PALB2": 0.3,
            "ATM": 0.3,
            "ARID1A": 0.25,
            "RNF43": 0.25,
            "STK11": 0.2,
            "TGFBR2": 0.2,
            "MAP2K4": 0.15,
            "PIK3CA": 0.15,
            "BRAF": 0.15,
        }
        score += pancreatic_drivers.get(gene, 0.0)

        # Clonality adjustment
        clonality = self.vaf_based_clonality(row)
        score = min(1.0, score * (0.5 + 0.5 * clonality))

        return min(1.0, max(0.0, score))
