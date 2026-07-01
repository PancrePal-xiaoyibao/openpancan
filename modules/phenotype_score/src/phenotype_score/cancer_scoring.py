"""
Cancer Phenotype Scoring Engine.

Scores genes by their relevance to pancreatic cancer phenotypes using
COSMIC, TCGA, OncoKB, and phenotype-to-gene association data.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pancreatic cancer phenotype → gene associations
# ---------------------------------------------------------------------------
PHENOTYPE_GENE_MAP: dict[str, dict[str, list[str]]] = {
    "pancreatic_ductal_adenocarcinoma": {
        "driver_genes": [
            "KRAS", "TP53", "SMAD4", "CDKN2A", "BRCA1", "BRCA2", "PALB2",
            "ATM", "ARID1A", "RNF43", "STK11", "TGFBR2", "MAP2K4",
        ],
        "frequently_mutated": [
            "GNAS", "KDM6A", "PIK3CA", "PTEN", "BRAF", "RB1", "ERBB2",
            "EGFR", "MET", "FGFR1", "CCND1", "MYC", "AKT1",
        ],
        "tumor_suppressor": [
            "TP53", "SMAD4", "CDKN2A", "PTEN", "RB1", "STK11",
            "ARID1A", "TGFBR2", "MAP2K4",
        ],
    },
}

# ---------------------------------------------------------------------------
# Gene-phenotype relevance scores (pancreatic cancer specific)
# ---------------------------------------------------------------------------
GENE_PHENOTYPE_BASE_SCORES: dict[str, float] = {
    # Tier 1 – strong pancreatic cancer driver genes
    "KRAS": 0.98,
    "TP53": 0.95,
    "SMAD4": 0.90,
    "CDKN2A": 0.88,
    # Tier 2 – established pancreatic cancer genes
    "BRCA1": 0.85,
    "BRCA2": 0.85,
    "PALB2": 0.80,
    "ATM": 0.78,
    "ARID1A": 0.75,
    "RNF43": 0.73,
    "STK11": 0.70,
    "TGFBR2": 0.68,
    "MAP2K4": 0.65,
    # Tier 3 – recurrently mutated in PAAD
    "GNAS": 0.60,
    "KDM6A": 0.58,
    "PIK3CA": 0.55,
    "PTEN": 0.55,
    "BRAF": 0.50,
    "RB1": 0.48,
    "ERBB2": 0.45,
    "EGFR": 0.42,
    "MET": 0.40,
    "MYC": 0.38,
    "AKT1": 0.35,
    "CCND1": 0.32,
    "FGFR1": 0.30,
}

# ---------------------------------------------------------------------------
# TCGA PAAD mutation frequencies
# ---------------------------------------------------------------------------
TCGA_PAAD_FREQ: dict[str, float] = {
    "KRAS": 0.92, "TP53": 0.72, "SMAD4": 0.32, "CDKN2A": 0.30,
    "BRCA1": 0.05, "BRCA2": 0.07, "PALB2": 0.03, "ATM": 0.05,
    "ARID1A": 0.07, "RNF43": 0.06, "STK11": 0.04, "TGFBR2": 0.05,
    "MAP2K4": 0.04, "GNAS": 0.10, "KDM6A": 0.08, "PIK3CA": 0.04,
    "PTEN": 0.03, "BRAF": 0.02, "RB1": 0.03, "ERBB2": 0.02,
    "EGFR": 0.02, "MET": 0.02, "MYC": 0.02, "AKT1": 0.02, "CCND1": 0.01,
}

# ---------------------------------------------------------------------------
# Cancer phenotype scoring class
# ---------------------------------------------------------------------------
class CancerPhenotypeScorer:
    """
    Scores genes by relevance to pancreatic cancer phenotypes.

    Combines gene-phenotype base scores, TCGA PAAD mutation frequencies,
    pathway membership, and functional annotations to produce a comprehensive
    gene-level phenotype score.
    """

    def __init__(self, cancer_type: str = "pancreatic_ductal_adenocarcinoma"):
        self.cancer_type = cancer_type
        self.base_scores = GENE_PHENOTYPE_BASE_SCORES
        self.tcga_freq = TCGA_PAAD_FREQ

    def score_gene_phenotype(self, gene: str) -> float:
        """
        Return the base phenotype score for a given gene.

        Falls back to TCGA frequency if no explicit score exists.
        """
        if gene in self.base_scores:
            return self.base_scores[gene]
        return self.tcga_freq.get(gene, 0.01) * 2.0  # scale frequency to 0-1 range

    def score_gene_batch(self, genes: pd.Series) -> pd.Series:
        """Score a series of gene symbols."""
        return genes.apply(self.score_gene_phenotype)

    def score_variant_phenotype(self, row: pd.Series) -> float:
        """
        Score a single variant for phenotype relevance.

        Combines gene-level score with consequence severity.
        """
        gene = str(row.get("SYMBOL", ""))
        base = self.score_gene_phenotype(gene)

        # Adjust for consequence severity
        consequence = str(row.get("Consequence", ""))
        impact = str(row.get("IMPACT", ""))

        impact_bonus = 0.0
        if impact == "HIGH":
            impact_bonus = 0.15
        elif impact == "MODERATE":
            impact_bonus = 0.08
        elif impact == "LOW":
            impact_bonus = 0.03

        # Cancer hotspot bonus
        if row.get("is_cancer_hotspot", False):
            impact_bonus += 0.10

        return min(1.0, base + impact_bonus)

    def run(self, vep_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
        """
        Run phenotype scoring on a VEP-annotated variant DataFrame.

        Parameters
        ----------
        vep_df : pd.DataFrame
            VEP-annotated variant DataFrame with SYMBOL column.

        Returns
        -------
        dict
            {'gene_scores': DataFrame, 'variant_scores': DataFrame}
        """
        logger.info("Running phenotype scoring on %d variants", len(vep_df))

        df = vep_df.copy()

        # ---- Gene-level scores ----
        if "SYMBOL" in df.columns:
            genes = df["SYMBOL"].drop_duplicates()
        else:
            genes = pd.Series(dtype=str)

        gene_scores_df = pd.DataFrame({
            "gene": genes.values,
            "phenotype_score": [self.score_gene_phenotype(g) for g in genes],
            "tcga_paad_freq": [self.tcga_freq.get(g, 0.0) for g in genes],
        })
        gene_scores_df = gene_scores_df.sort_values("phenotype_score", ascending=False)
        gene_scores_df["rank"] = range(1, len(gene_scores_df) + 1)

        # ---- Variant-level scores ----
        df["phenotype_score"] = df.apply(self.score_variant_phenotype, axis=1)
        # Keep relevant columns
        var_cols = [c for c in [
            "Uploaded_variation", "Location", "SYMBOL", "Gene", "Consequence",
            "IMPACT", "HGVSp", "AF", "CLIN_SIG", "phenotype_score",
        ] if c in df.columns]
        variant_scores_df = df[var_cols].sort_values("phenotype_score", ascending=False)
        variant_scores_df["rank"] = range(1, len(variant_scores_df) + 1)

        logger.info(
            "Phenotype scoring complete: %d genes, %d variants scored",
            len(gene_scores_df), len(variant_scores_df),
        )

        return {
            "gene_scores": gene_scores_df,
            "variant_scores": variant_scores_df,
        }
