"""
Cancer annotation enrichment for pancreatic cancer VEP output.

Provides cancer-specific annotation data including COSMIC IDs, TCGA PAAD
frequencies, OncoKB levels, and pancreatic cancer driver gene information.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pancreatic Cancer Driver Genes
# ---------------------------------------------------------------------------
PANCREATIC_CANCER_DRIVER_GENES: list[str] = [
    "KRAS",
    "TP53",
    "SMAD4",
    "CDKN2A",
    "BRCA1",
    "BRCA2",
    "PALB2",
    "ATM",
    "ARID1A",
    "RNF43",
    "STK11",
    "TGFBR2",
    "MAP2K4",
]

# ---------------------------------------------------------------------------
# KRAS Hotspot Mutations (pancreatic cancer)
# ---------------------------------------------------------------------------
KRAS_HOTSPOT_MUTATIONS: dict[str, dict[str, Any]] = {
    "G12D": {
        "cosmic_id": "COSM521",
        "cancer_type": "pancreatic_ductal_adenocarcinoma",
        "frequency_score": 0.36,
        "oncokb_level": 1,
        "description": "KRAS G12D – most common pancreatic cancer mutation",
    },
    "G12V": {
        "cosmic_id": "COSM520",
        "cancer_type": "pancreatic_ductal_adenocarcinoma",
        "frequency_score": 0.30,
        "oncokb_level": 1,
        "description": "KRAS G12V – second most common pancreatic cancer mutation",
    },
    "G12C": {
        "cosmic_id": "COSM516",
        "cancer_type": "pancreatic_ductal_adenocarcinoma",
        "frequency_score": 0.03,
        "oncokb_level": 1,
        "description": "KRAS G12C – targetable with sotorasib / adagrasib",
    },
    "G12R": {
        "cosmic_id": "COSM518",
        "cancer_type": "pancreatic_ductal_adenocarcinoma",
        "frequency_score": 0.14,
        "oncokb_level": 1,
        "description": "KRAS G12R – pancreatic cancer hotspot",
    },
    "Q61H": {
        "cosmic_id": "COSM549",
        "cancer_type": "pancreatic_ductal_adenocarcinoma",
        "frequency_score": 0.05,
        "oncokb_level": 2,
        "description": "KRAS Q61H – pancreatic cancer hotspot",
    },
    "G13D": {
        "cosmic_id": "COSM532",
        "cancer_type": "pancreatic_ductal_adenocarcinoma",
        "frequency_score": 0.02,
        "oncokb_level": 3,
        "description": "KRAS G13D – rare pancreatic cancer mutation",
    },
}

# ---------------------------------------------------------------------------
# COSMIC Cancer Gene Census – pancreatic-relevant genes
# ---------------------------------------------------------------------------
COSMIC_CANCER_GENE_CENSUS: dict[str, dict[str, Any]] = {
    "KRAS": {
        "tier": 1,
        "role": "oncogene",
        "somatic": True,
        "germline": False,
        "tumour_types_somatic": ["pancreatic carcinoma"],
    },
    "TP53": {
        "tier": 1,
        "role": "TSG",
        "somatic": True,
        "germline": True,
        "tumour_types_somatic": ["pancreatic carcinoma", "many"],
    },
    "SMAD4": {
        "tier": 1,
        "role": "TSG",
        "somatic": True,
        "germline": True,
        "tumour_types_somatic": ["pancreatic carcinoma", "colorectal"],
    },
    "CDKN2A": {
        "tier": 1,
        "role": "TSG",
        "somatic": True,
        "germline": True,
        "tumour_types_somatic": ["pancreatic carcinoma", "melanoma"],
    },
    "BRCA1": {
        "tier": 1,
        "role": "TSG",
        "somatic": True,
        "germline": True,
        "tumour_types_somatic": ["pancreatic carcinoma", "breast", "ovarian"],
    },
    "BRCA2": {
        "tier": 1,
        "role": "TSG",
        "somatic": True,
        "germline": True,
        "tumour_types_somatic": ["pancreatic carcinoma", "breast", "ovarian", "prostate"],
    },
    "PALB2": {
        "tier": 1,
        "role": "TSG",
        "somatic": True,
        "germline": True,
        "tumour_types_somatic": ["pancreatic carcinoma", "breast"],
    },
    "ATM": {
        "tier": 1,
        "role": "TSG",
        "somatic": True,
        "germline": True,
        "tumour_types_somatic": ["pancreatic carcinoma", "breast"],
    },
    "ARID1A": {
        "tier": 1,
        "role": "TSG",
        "somatic": True,
        "germline": False,
        "tumour_types_somatic": ["pancreatic carcinoma", "ovarian clear cell"],
    },
    "RNF43": {
        "tier": 1,
        "role": "TSG",
        "somatic": True,
        "germline": False,
        "tumour_types_somatic": ["pancreatic carcinoma", "colorectal"],
    },
    "STK11": {
        "tier": 1,
        "role": "TSG",
        "somatic": True,
        "germline": True,
        "tumour_types_somatic": ["pancreatic carcinoma", "NSCLC"],
    },
    "TGFBR2": {
        "tier": 1,
        "role": "TSG",
        "somatic": True,
        "germline": False,
        "tumour_types_somatic": ["pancreatic carcinoma", "colorectal"],
    },
    "MAP2K4": {
        "tier": 2,
        "role": "TSG",
        "somatic": True,
        "germline": False,
        "tumour_types_somatic": ["pancreatic carcinoma"],
    },
}

# ---------------------------------------------------------------------------
# TCGA PAAD Mutation Frequencies (per gene)
# ---------------------------------------------------------------------------
TCGA_PAAD_FREQUENCIES: dict[str, float] = {
    "KRAS": 0.92,
    "TP53": 0.72,
    "SMAD4": 0.32,
    "CDKN2A": 0.30,
    "BRCA1": 0.05,
    "BRCA2": 0.07,
    "PALB2": 0.03,
    "ATM": 0.05,
    "ARID1A": 0.07,
    "RNF43": 0.06,
    "STK11": 0.04,
    "TGFBR2": 0.05,
    "MAP2K4": 0.04,
    "GNAS": 0.10,
    "KDM6A": 0.08,
    "PIK3CA": 0.04,
    "PTEN": 0.03,
    "BRAF": 0.02,
    "RB1": 0.03,
    "ERBB2": 0.02,
    "EGFR": 0.02,
    "MET": 0.02,
}

# ---------------------------------------------------------------------------
# OncoKB Level mapping
# ---------------------------------------------------------------------------
_ONCOKB_LEVEL_MAP: dict[str, int] = {
    "KRAS": 1,
    "TP53": 2,
    "SMAD4": 2,
    "CDKN2A": 2,
    "BRCA1": 1,
    "BRCA2": 1,
    "PALB2": 2,
    "ATM": 2,
    "ARID1A": 3,
    "RNF43": 3,
    "STK11": 3,
    "TGFBR2": 3,
    "MAP2K4": 4,
    "GNAS": 4,
    "KDM6A": 4,
    "PIK3CA": 2,
    "PTEN": 2,
    "BRAF": 1,
    "RB1": 2,
    "ERBB2": 2,
    "EGFR": 2,
    "MET": 3,
}

# ---------------------------------------------------------------------------
# Pancreatic cancer pathway genes
# ---------------------------------------------------------------------------
PANCREATIC_CANCER_PATHWAYS: dict[str, list[str]] = {
    "KRAS_signaling": ["KRAS", "NRAS", "HRAS", "BRAF", "RAF1", "MAP2K1", "MAP2K2",
                       "MAP2K4", "MAPK1", "MAPK3", "NF1", "RASA1"],
    "TP53_pathway": ["TP53", "MDM2", "MDM4", "CDKN2A", "ATM", "ATR", "CHEK1", "CHEK2"],
    "TGF_beta_SMAD": ["TGFBR1", "TGFBR2", "SMAD2", "SMAD3", "SMAD4"],
    "WNT_signaling": ["RNF43", "CTNNB1", "APC", "AXIN1", "AXIN2", "TCF7L2"],
    "DNA_damage_repair": ["BRCA1", "BRCA2", "PALB2", "ATM", "ATR", "CHEK2", "RAD51C",
                          "RAD51D", "FANCA", "FANCC"],
    "chromatin_remodeling": ["ARID1A", "ARID1B", "ARID2", "SMARCA4", "SMARCA2", "PBRM1",
                             "SETD2", "KDM6A"],
    "cell_cycle": ["CDKN2A", "CDKN2B", "RB1", "CCND1", "CDK4", "CDK6", "E2F1"],
    "PI3K_AKT": ["PIK3CA", "PIK3R1", "PTEN", "AKT1", "AKT2", "MTOR"],
}


# ---------------------------------------------------------------------------
# Main annotation function
# ---------------------------------------------------------------------------
def add_cancer_annotations(variants_df: pd.DataFrame) -> pd.DataFrame:
    """
    Enrich a variants DataFrame with pancreatic cancer-specific annotations.

    Adds columns:
        cosmic_id           – COSMIC mutation ID (if found)
        tcga_paad_freq      – TCGA PAAD mutation frequency for the gene
        oncokb_level        – OncoKB therapeutic level (1-4)
        is_cancer_hotspot   – True if mutation is a known hotspot
        is_driver_gene      – True if gene is a pancreatic cancer driver
        is_pancreatic_cancer_gene – True if gene appears in COSMIC CGC for pancreatic
        cancer_pathway      – Primary pathway membership

    Parameters
    ----------
    variants_df : pd.DataFrame
        DataFrame with at least columns:
        - SYMBOL  (gene symbol)
        - HGVSp   (protein change, e.g. "p.Gly12Asp")

    Returns
    -------
    pd.DataFrame
        The input DataFrame with added cancer annotation columns.
    """
    logger.info("Adding cancer annotations to %d variants", len(variants_df))

    # --- Ensure required columns exist ------------------------------------
    if "SYMBOL" not in variants_df.columns:
        logger.warning("No SYMBOL column; skipping cancer annotations")
        return variants_df

    # --- cosmos_id --------------------------------------------------------
    variants_df["cosmic_id"] = variants_df.apply(_lookup_cosmic_id, axis=1)

    # --- tcga_paad_freq ---------------------------------------------------
    variants_df["tcga_paad_freq"] = variants_df["SYMBOL"].map(
        lambda g: TCGA_PAAD_FREQUENCIES.get(g, 0.0)
    )

    # --- oncokb_level -----------------------------------------------------
    variants_df["oncokb_level"] = variants_df["SYMBOL"].map(
        lambda g: _ONCOKB_LEVEL_MAP.get(g, 4)
    )

    # --- is_cancer_hotspot -------------------------------------------------
    variants_df["is_cancer_hotspot"] = variants_df.apply(_is_hotspot, axis=1)

    # --- is_driver_gene ----------------------------------------------------
    variants_df["is_driver_gene"] = variants_df["SYMBOL"].isin(
        PANCREATIC_CANCER_DRIVER_GENES
    )

    # --- is_pancreatic_cancer_gene -----------------------------------------
    variants_df["is_pancreatic_cancer_gene"] = variants_df["SYMBOL"].apply(
        _in_pancreatic_cgc
    )

    # --- cancer_pathway ----------------------------------------------------
    variants_df["cancer_pathway"] = variants_df["SYMBOL"].apply(_primary_pathway)

    logger.info(
        "Cancer annotations added: %d hotspot, %d driver genes identified",
        variants_df["is_cancer_hotspot"].sum(),
        variants_df["is_driver_gene"].sum(),
    )

    return variants_df


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _lookup_cosmic_id(row: pd.Series) -> str:
    """Find COSMIC ID by matching gene + protein change against hotspot DB."""
    gene = str(row.get("SYMBOL", ""))
    hgvsp = str(row.get("HGVSp", ""))

    if gene == "KRAS" and hgvsp:
        for mutation, info in KRAS_HOTSPOT_MUTATIONS.items():
            if mutation in hgvsp:
                return info["cosmic_id"]

    # Generic COSMIC placeholder for pancreatic driver genes
    if gene in COSMIC_CANCER_GENE_CENSUS:
        return f"COSM_{gene}"

    return ""


def _is_hotspot(row: pd.Series) -> bool:
    """Determine if a variant is a known cancer hotspot mutation."""
    gene = str(row.get("SYMBOL", ""))
    hgvsp = str(row.get("HGVSp", ""))

    if gene == "KRAS" and hgvsp:
        for mutation in KRAS_HOTSPOT_MUTATIONS:
            if mutation in hgvsp:
                return True

    # Common TP53 hotspot positions (R175, R248, R273, etc.)
    if gene == "TP53" and hgvsp:
        tp53_hotspots = ["R175", "R248", "R273", "R282", "G245"]
        for hs in tp53_hotspots:
            if hs in hgvsp:
                return True

    return False


def _in_pancreatic_cgc(gene: str) -> bool:
    """Check if gene is in COSMIC Cancer Gene Census as pancreatic-relevant."""
    if gene not in COSMIC_CANCER_GENE_CENSUS:
        return False
    cgc_entry = COSMIC_CANCER_GENE_CENSUS[gene]
    tumour_types = cgc_entry.get("tumour_types_somatic", [])
    return any("pancreatic" in t.lower() for t in tumour_types)


def _primary_pathway(gene: str) -> str:
    """Find the primary pancreatic cancer pathway for a gene."""
    for pathway_name, gene_list in PANCREATIC_CANCER_PATHWAYS.items():
        if gene in gene_list:
            return pathway_name
    return ""
