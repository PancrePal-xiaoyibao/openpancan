"""
Cancer Driver Ranking engine for pancreatic cancer variants.

Implements a weighted multi-criteria ranking system with two-pass scoring
to prioritize putative cancer driver mutations.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from variant_rank.somatic_scoring import SomaticVariantScorer

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# KRAS hotspot mutations
# ---------------------------------------------------------------------------
KRAS_HOTSPOT_MUTATIONS: dict[str, dict[str, Any]] = {
    "G12D": {
        "cosmic_id": "COSM521",
        "cosmic_count": 28500,
        "cancer_type": "pancreatic_ductal_adenocarcinoma",
        "frequency_paad": 0.36,
        "oncokb_level": 1,
        "drug_association": "Pan-KRAS inhibitors",
    },
    "G12V": {
        "cosmic_id": "COSM520",
        "cosmic_count": 24000,
        "cancer_type": "pancreatic_ductal_adenocarcinoma",
        "frequency_paad": 0.30,
        "oncokb_level": 1,
        "drug_association": "Pan-KRAS inhibitors",
    },
    "G12R": {
        "cosmic_id": "COSM518",
        "cosmic_count": 11000,
        "cancer_type": "pancreatic_ductal_adenocarcinoma",
        "frequency_paad": 0.14,
        "oncokb_level": 1,
        "drug_association": "Pan-KRAS inhibitors",
    },
    "Q61H": {
        "cosmic_id": "COSM549",
        "cosmic_count": 4000,
        "cancer_type": "pancreatic_ductal_adenocarcinoma",
        "frequency_paad": 0.05,
        "oncokb_level": 2,
        "drug_association": "Pan-KRAS inhibitors (investigational)",
    },
    "G12C": {
        "cosmic_id": "COSM516",
        "cosmic_count": 2500,
        "cancer_type": "pancreatic_ductal_adenocarcinoma",
        "frequency_paad": 0.03,
        "oncokb_level": 1,
        "drug_association": "Sotorasib, Adagrasib",
    },
    "G13D": {
        "cosmic_id": "COSM532",
        "cosmic_count": 1800,
        "cancer_type": "pancreatic_ductal_adenocarcinoma",
        "frequency_paad": 0.02,
        "oncokb_level": 3,
        "drug_association": "Investigational",
    },
    "Q61R": {
        "cosmic_id": "COSM550",
        "cosmic_count": 1500,
        "cancer_type": "pancreatic_ductal_adenocarcinoma",
        "frequency_paad": 0.02,
        "oncokb_level": 3,
        "drug_association": "Investigational",
    },
    "A146T": {
        "cosmic_id": "COSM19405",
        "cosmic_count": 800,
        "cancer_type": "pancreatic_ductal_adenocarcinoma",
        "frequency_paad": 0.01,
        "oncokb_level": 3,
        "drug_association": "Investigational",
    },
}

# ---------------------------------------------------------------------------
# Pancreatic Cancer Driver Theta Weights
# ---------------------------------------------------------------------------
PANCREATIC_CANCER_DRIVER_THETA: dict[str, float] = {
    "clinvar_significance": 0.20,
    "consequence": 0.15,
    "vaf": 0.05,
    "cancer_hotspot": 0.15,
    "cosmic_count": 0.10,
    "oncokb_level": 0.10,
    "tcga_frequency": 0.08,
    "pathway_membership": 0.07,
    "ppi": 0.05,
    "gene_phenotype": 0.05,
}

# ---------------------------------------------------------------------------
# ClinVar clinical significance scoring
# ---------------------------------------------------------------------------
CLINVAR_SIGNIFICANCE_SCORES: dict[str, float] = {
    "pathogenic": 1.0,
    "likely_pathogenic": 0.8,
    "pathogenic/likely_pathogenic": 0.9,
    "uncertain_significance": 0.3,
    "vus": 0.3,
    "conflicting_interpretations": 0.4,
    "likely_benign": 0.1,
    "benign": 0.0,
    "benign/likely_benign": 0.05,
    "not_provided": 0.2,
}

# ---------------------------------------------------------------------------
# Consequence severity scoring
# ---------------------------------------------------------------------------
CONSEQUENCE_SCORES: dict[str, float] = {
    "stop_gained": 1.0,
    "frameshift_variant": 1.0,
    "splice_acceptor_variant": 0.95,
    "splice_donor_variant": 0.95,
    "stop_lost": 0.9,
    "start_lost": 0.8,
    "inframe_insertion": 0.6,
    "inframe_deletion": 0.6,
    "missense_variant": 0.5,
    "protein_altering_variant": 0.4,
    "splice_region_variant": 0.2,
    "synonymous_variant": 0.05,
    "intron_variant": 0.01,
    "5_prime_UTR_variant": 0.05,
    "3_prime_UTR_variant": 0.05,
    "upstream_gene_variant": 0.02,
    "downstream_gene_variant": 0.02,
    "intergenic_variant": 0.0,
}

# ---------------------------------------------------------------------------
# OncoKB level scoring
# ---------------------------------------------------------------------------
ONCOKB_LEVEL_SCORES: dict[int, float] = {
    1: 1.0,
    2: 0.75,
    3: 0.4,
    4: 0.1,
}

# ---------------------------------------------------------------------------
# Pathway membership (pancreatic cancer pathways)
# ---------------------------------------------------------------------------
PANCREATIC_PATHWAYS: dict[str, list[str]] = {
    "KRAS_signaling": ["KRAS", "NRAS", "HRAS", "BRAF", "RAF1", "MAP2K1", "MAP2K2",
                       "MAP2K4", "MAPK1", "MAPK3", "NF1", "RASA1"],
    "TP53_pathway": ["TP53", "MDM2", "MDM4", "CDKN2A", "ATM", "ATR", "CHEK1", "CHEK2"],
    "TGF_beta_SMAD": ["TGFBR1", "TGFBR2", "SMAD2", "SMAD3", "SMAD4"],
    "WNT_signaling": ["RNF43", "CTNNB1", "APC", "AXIN1", "AXIN2", "TCF7L2"],
    "DNA_damage_repair": ["BRCA1", "BRCA2", "PALB2", "ATM", "ATR", "CHEK2", "RAD51C",
                          "RAD51D", "FANCA", "FANCC", "BRIP1", "BARD1"],
    "chromatin_remodeling": ["ARID1A", "ARID1B", "ARID2", "SMARCA4", "SMARCA2",
                             "PBRM1", "SETD2", "KDM6A"],
    "cell_cycle": ["CDKN2A", "CDKN2B", "RB1", "CCND1", "CDK4", "CDK6", "E2F1",
                   "CCNE1", "MYC"],
    "PI3K_AKT_mTOR": ["PIK3CA", "PIK3R1", "PTEN", "AKT1", "AKT2", "MTOR", "TSC1", "TSC2"],
}

# Build gene → pathway reverse mapping
_GENE_TO_PATHWAY: dict[str, str] = {}
for _pathway, _genes in PANCREATIC_PATHWAYS.items():
    for _g in _genes:
        _GENE_TO_PATHWAY[_g] = _pathway


# ---------------------------------------------------------------------------
# CancerDriverRanker class
# ---------------------------------------------------------------------------
class CancerDriverRanker:
    """
    Ranks variants by their likelihood of being pancreatic cancer driver
    mutations using a weighted multi-criteria scoring system.

    Implements two-pass scoring:
        1. Pass 1: Compute raw scores for each scoring dimension.
        2. Pass 2: Normalize scores and apply weighting, then rank.
    """

    def __init__(self, cancer_type: str = "pancreatic_ductal_adenocarcinoma"):
        self.cancer_type = cancer_type
        self.theta = PANCREATIC_CANCER_DRIVER_THETA
        self.somatic_scorer = SomaticVariantScorer(cancer_type)

    # ------------------------------------------------------------------
    # Individual scoring functions
    # ------------------------------------------------------------------

    @staticmethod
    def score_clinvar_significance(row: pd.Series) -> float:
        """Score variant based on ClinVar clinical significance."""
        clin_sig = str(row.get("CLIN_SIG", "")).lower()
        return CLINVAR_SIGNIFICANCE_SCORES.get(clin_sig, 0.2)

    @staticmethod
    def score_consequence(row: pd.Series) -> float:
        """Score variant based on molecular consequence severity."""
        consequence = str(row.get("Consequence", "")).strip()
        # Split multiple consequences, take the most severe
        if "&" in consequence:
            cons_list = [c.strip() for c in consequence.split("&")]
            return max(CONSEQUENCE_SCORES.get(c, 0.0) for c in cons_list)
        return CONSEQUENCE_SCORES.get(consequence, 0.0)

    def score_vaf(self, row: pd.Series) -> float:
        """Score based on variant allele fraction (clonality proxy)."""
        return self.somatic_scorer.vaf_based_clonality(row)

    def score_cancer_hotspot(self, row: pd.Series) -> float:
        """Score based on whether variant matches a known cancer hotspot."""
        hotspot_score, _ = self.somatic_scorer.hotspot_match(row)

        # Also check KRAS specific hotspots
        gene = str(row.get("SYMBOL", ""))
        hgvsp = str(row.get("HGVSp", ""))
        if gene == "KRAS":
            for mutation in KRAS_HOTSPOT_MUTATIONS:
                if mutation in hgvsp:
                    hotspot_score = max(hotspot_score, 1.0)

        return hotspot_score

    @staticmethod
    def score_cosmic_count(row: pd.Series) -> float:
        """Score based on number of COSMIC occurrences (normalized)."""
        gene = str(row.get("SYMBOL", ""))
        hgvsp = str(row.get("HGVSp", ""))

        if gene == "KRAS":
            for mutation, data in KRAS_HOTSPOT_MUTATIONS.items():
                if mutation in hgvsp:
                    count = data.get("cosmic_count", 0)
                    return min(1.0, count / 30000.0)

        # Use TCGA frequency as proxy
        cosmic_id = str(row.get("cosmic_id", ""))
        if cosmic_id and cosmic_id != "nan":
            return 0.5  # Has COSMIC entry but not in hotspot DB

        return 0.0

    @staticmethod
    def score_oncokb_level(row: pd.Series) -> float:
        """Score based on OncoKB therapeutic level."""
        oncokb = row.get("oncokb_level", None)
        try:
            level = int(oncokb) if oncokb is not None and str(oncokb) != "nan" else 4
        except (ValueError, TypeError):
            level = 4
        return ONCOKB_LEVEL_SCORES.get(level, 0.1)

    @staticmethod
    def score_frequency(row: pd.Series) -> float:
        """Score based on TCGA PAAD mutation frequency."""
        freq = row.get("tcga_paad_freq", None)
        try:
            f = float(freq) if freq is not None and str(freq) != "nan" else 0.0
        except (ValueError, TypeError):
            f = 0.0
        return min(1.0, f)

    @staticmethod
    def score_pathway_membership(row: pd.Series) -> float:
        """Score based on membership in pancreatic cancer pathways."""
        gene = str(row.get("SYMBOL", ""))
        pathway = _GENE_TO_PATHWAY.get(gene, "")

        if not pathway:
            return 0.0

        # Higher score for key pathways
        key_pathway_scores = {
            "KRAS_signaling": 1.0,
            "TP53_pathway": 1.0,
            "TGF_beta_SMAD": 0.9,
            "DNA_damage_repair": 0.85,
            "cell_cycle": 0.8,
            "WNT_signaling": 0.7,
            "chromatin_remodeling": 0.6,
            "PI3K_AKT_mTOR": 0.6,
        }
        return key_pathway_scores.get(pathway, 0.3)

    @staticmethod
    def score_ppi(row: pd.Series, ppi_scores: dict[str, float] | None = None) -> float:
        """
        Score based on protein-protein interaction network.

        If external PPI scores are provided, use them. Otherwise, estimate
        based on known interaction partners of pancreatic cancer drivers.
        """
        if ppi_scores is not None:
            gene = str(row.get("SYMBOL", ""))
            return ppi_scores.get(gene, 0.0)

        # Fallback: known high-PPI genes in pancreatic cancer
        high_ppi_genes = {"TP53": 0.95, "BRCA1": 0.85, "BRCA2": 0.85, "SMAD4": 0.8,
                          "ATM": 0.75, "CDKN2A": 0.7, "KRAS": 0.65, "PIK3CA": 0.55,
                          "PTEN": 0.55, "PALB2": 0.5, "ARID1A": 0.45}
        gene = str(row.get("SYMBOL", ""))
        return high_ppi_genes.get(gene, 0.1)

    @staticmethod
    def score_gene_phenotype(row: pd.Series,
                             gene_scores: dict[str, float] | None = None) -> float:
        """
        Score based on gene-level phenotype matching.

        If external gene-phenotype scores are provided, use them.
        """
        if gene_scores is not None:
            gene = str(row.get("SYMBOL", ""))
            return gene_scores.get(gene, 0.0)
        return 0.0

    # ------------------------------------------------------------------
    # Two-pass scoring
    # ------------------------------------------------------------------

    def score_variants(
        self,
        df: pd.DataFrame,
        ppi_scores: dict[str, float] | None = None,
        gene_scores: dict[str, float] | None = None,
    ) -> pd.DataFrame:
        """
        First pass: compute raw scores for each scoring dimension.

        Returns DataFrame with added score columns.
        """
        logger.info("Pass 1: Computing raw scores for %d variants", len(df))

        df = df.copy()

        # Compute each score dimension
        df["score_clinvar"] = df.apply(self.score_clinvar_significance, axis=1)
        df["score_consequence"] = df.apply(self.score_consequence, axis=1)
        df["score_vaf"] = df.apply(self.score_vaf, axis=1)
        df["score_hotspot"] = df.apply(self.score_cancer_hotspot, axis=1)
        df["score_cosmic"] = df.apply(self.score_cosmic_count, axis=1)
        df["score_oncokb"] = df.apply(self.score_oncokb_level, axis=1)
        df["score_tcga_freq"] = df.apply(self.score_frequency, axis=1)
        df["score_pathway"] = df.apply(self.score_pathway_membership, axis=1)
        df["score_ppi_dim"] = df.apply(
            lambda r: self.score_ppi(r, ppi_scores), axis=1
        )
        df["score_phenotype_dim"] = df.apply(
            lambda r: self.score_gene_phenotype(r, gene_scores), axis=1
        )

        return df

    def rank_variants(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Second pass: apply weighted scoring and rank variants.

        Returns DataFrame sorted by total_score descending, with rank column.
        """
        logger.info("Pass 2: Computing weighted total scores and ranking")

        df = df.copy()

        # Compute weighted total score
        df["total_score"] = (
            self.theta["clinvar_significance"] * df["score_clinvar"]
            + self.theta["consequence"] * df["score_consequence"]
            + self.theta["vaf"] * df["score_vaf"]
            + self.theta["cancer_hotspot"] * df["score_hotspot"]
            + self.theta["cosmic_count"] * df["score_cosmic"]
            + self.theta["oncokb_level"] * df["score_oncokb"]
            + self.theta["tcga_frequency"] * df["score_tcga_freq"]
            + self.theta["pathway_membership"] * df["score_pathway"]
            + self.theta["ppi"] * df["score_ppi_dim"]
            + self.theta["gene_phenotype"] * df["score_phenotype_dim"]
        )

        # Sort by total score descending
        df = df.sort_values("total_score", ascending=False).reset_index(drop=True)

        # Add rank
        df["rank"] = range(1, len(df) + 1)

        # Add tier classification
        df["tier"] = df["total_score"].apply(self._classify_tier)

        logger.info(
            "Ranking complete: %d variants ranked (top score: %.4f)",
            len(df),
            df["total_score"].max() if len(df) > 0 else 0.0,
        )

        return df

    @staticmethod
    def _classify_tier(score: float) -> str:
        """Classify a variant into a tier based on total score."""
        if score >= 0.7:
            return "Tier_1_Strong"
        elif score >= 0.5:
            return "Tier_2_Potential"
        elif score >= 0.3:
            return "Tier_3_Uncertain"
        else:
            return "Tier_4_VUS"

    # ------------------------------------------------------------------
    # Convenience method
    # ------------------------------------------------------------------

    def run(
        self,
        df: pd.DataFrame,
        ppi_scores: dict[str, float] | None = None,
        gene_scores: dict[str, float] | None = None,
    ) -> pd.DataFrame:
        """
        Run the full two-pass scoring and ranking pipeline on a variant DataFrame.

        Returns the ranked and scored DataFrame.
        """
        scored_df = self.score_variants(df, ppi_scores, gene_scores)
        ranked_df = self.rank_variants(scored_df)
        return ranked_df
