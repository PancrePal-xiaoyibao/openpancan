"""
Cancer PPI (Protein-Protein Interaction) scoring for pancreatic cancer.

Scores genes based on their interaction network with known pancreatic
cancer driver genes and pathway members. Uses curated PPI data for
pancreatic cancer-related protein interactions.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pancreatic Cancer PPI Network (curated)
#
# Each gene maps to a list of known interaction partners with an
# interaction confidence score (0.0–1.0).
# Data sourced from STRING, BioGRID, and literature-curated interactions
# relevant to pancreatic ductal adenocarcinoma.
# ---------------------------------------------------------------------------
PANCREATIC_CANCER_PPI: dict[str, list[dict[str, Any]]] = {
    "KRAS": [
        {"partner": "RAF1", "score": 0.99, "pathway": "MAPK_signaling"},
        {"partner": "BRAF", "score": 0.99, "pathway": "MAPK_signaling"},
        {"partner": "PIK3CA", "score": 0.95, "pathway": "PI3K_AKT"},
        {"partner": "RALGDS", "score": 0.95, "pathway": "RAL_signaling"},
        {"partner": "RASSF1", "score": 0.85, "pathway": "apoptosis"},
        {"partner": "TIAM1", "score": 0.80, "pathway": "RAL_signaling"},
        {"partner": "SOS1", "score": 0.90, "pathway": "MAPK_signaling"},
        {"partner": "GRB2", "score": 0.90, "pathway": "MAPK_signaling"},
    ],
    "TP53": [
        {"partner": "MDM2", "score": 0.99, "pathway": "TP53_pathway"},
        {"partner": "MDM4", "score": 0.98, "pathway": "TP53_pathway"},
        {"partner": "ATM", "score": 0.97, "pathway": "DNA_damage"},
        {"partner": "CHEK2", "score": 0.95, "pathway": "DNA_damage"},
        {"partner": "BAX", "score": 0.90, "pathway": "apoptosis"},
        {"partner": "CDKN1A", "score": 0.95, "pathway": "cell_cycle"},
        {"partner": "BBC3", "score": 0.88, "pathway": "apoptosis"},
        {"partner": "PML", "score": 0.85, "pathway": "apoptosis"},
    ],
    "SMAD4": [
        {"partner": "SMAD2", "score": 0.99, "pathway": "TGF_beta"},
        {"partner": "SMAD3", "score": 0.99, "pathway": "TGF_beta"},
        {"partner": "TGFBR1", "score": 0.92, "pathway": "TGF_beta"},
        {"partner": "TGFBR2", "score": 0.93, "pathway": "TGF_beta"},
        {"partner": "SKIL", "score": 0.85, "pathway": "TGF_beta"},
        {"partner": "SP1", "score": 0.80, "pathway": "transcription"},
    ],
    "CDKN2A": [
        {"partner": "CDK4", "score": 0.99, "pathway": "cell_cycle"},
        {"partner": "CDK6", "score": 0.99, "pathway": "cell_cycle"},
        {"partner": "MDM2", "score": 0.90, "pathway": "TP53_pathway"},
        {"partner": "CCND1", "score": 0.85, "pathway": "cell_cycle"},
        {"partner": "RB1", "score": 0.80, "pathway": "cell_cycle"},
    ],
    "BRCA1": [
        {"partner": "BRCA2", "score": 0.99, "pathway": "DNA_damage"},
        {"partner": "RAD51", "score": 0.99, "pathway": "DNA_damage"},
        {"partner": "BARD1", "score": 0.99, "pathway": "DNA_damage"},
        {"partner": "ATM", "score": 0.95, "pathway": "DNA_damage"},
        {"partner": "CHEK2", "score": 0.93, "pathway": "DNA_damage"},
        {"partner": "PALB2", "score": 0.92, "pathway": "DNA_damage"},
        {"partner": "BRIP1", "score": 0.90, "pathway": "DNA_damage"},
    ],
    "BRCA2": [
        {"partner": "BRCA1", "score": 0.99, "pathway": "DNA_damage"},
        {"partner": "RAD51", "score": 0.99, "pathway": "DNA_damage"},
        {"partner": "PALB2", "score": 0.98, "pathway": "DNA_damage"},
        {"partner": "FANCD2", "score": 0.90, "pathway": "Fanconi_anemia"},
        {"partner": "FANCA", "score": 0.88, "pathway": "Fanconi_anemia"},
    ],
    "PALB2": [
        {"partner": "BRCA2", "score": 0.98, "pathway": "DNA_damage"},
        {"partner": "BRCA1", "score": 0.92, "pathway": "DNA_damage"},
        {"partner": "RAD51", "score": 0.90, "pathway": "DNA_damage"},
        {"partner": "KEAP1", "score": 0.80, "pathway": "oxidative_stress"},
    ],
    "ATM": [
        {"partner": "TP53", "score": 0.97, "pathway": "DNA_damage"},
        {"partner": "CHEK2", "score": 0.97, "pathway": "DNA_damage"},
        {"partner": "BRCA1", "score": 0.95, "pathway": "DNA_damage"},
        {"partner": "H2AX", "score": 0.95, "pathway": "DNA_damage"},
        {"partner": "NBN", "score": 0.94, "pathway": "DNA_damage"},
        {"partner": "MRE11", "score": 0.93, "pathway": "DNA_damage"},
    ],
    "ARID1A": [
        {"partner": "SMARCA4", "score": 0.95, "pathway": "chromatin_remodeling"},
        {"partner": "SMARCA2", "score": 0.93, "pathway": "chromatin_remodeling"},
        {"partner": "PBRM1", "score": 0.90, "pathway": "chromatin_remodeling"},
        {"partner": "TP53", "score": 0.75, "pathway": "chromatin_remodeling"},
    ],
    "RNF43": [
        {"partner": "FZD5", "score": 0.90, "pathway": "WNT"},
        {"partner": "LRP6", "score": 0.88, "pathway": "WNT"},
        {"partner": "ZNRF3", "score": 0.95, "pathway": "WNT"},
        {"partner": "CTNNB1", "score": 0.80, "pathway": "WNT"},
    ],
    "TGFBR2": [
        {"partner": "TGFBR1", "score": 0.99, "pathway": "TGF_beta"},
        {"partner": "SMAD2", "score": 0.98, "pathway": "TGF_beta"},
        {"partner": "SMAD3", "score": 0.98, "pathway": "TGF_beta"},
        {"partner": "TGFB1", "score": 0.95, "pathway": "TGF_beta"},
        {"partner": "SMAD4", "score": 0.93, "pathway": "TGF_beta"},
    ],
    "PIK3CA": [
        {"partner": "PIK3R1", "score": 0.99, "pathway": "PI3K_AKT"},
        {"partner": "AKT1", "score": 0.98, "pathway": "PI3K_AKT"},
        {"partner": "KRAS", "score": 0.95, "pathway": "PI3K_AKT"},
        {"partner": "PTEN", "score": 0.90, "pathway": "PI3K_AKT"},
        {"partner": "MTOR", "score": 0.85, "pathway": "PI3K_AKT"},
    ],
    "PTEN": [
        {"partner": "PIK3CA", "score": 0.90, "pathway": "PI3K_AKT"},
        {"partner": "AKT1", "score": 0.95, "pathway": "PI3K_AKT"},
        {"partner": "TP53", "score": 0.80, "pathway": "PI3K_AKT"},
    ],
    "BRAF": [
        {"partner": "KRAS", "score": 0.99, "pathway": "MAPK_signaling"},
        {"partner": "MAP2K1", "score": 0.99, "pathway": "MAPK_signaling"},
        {"partner": "MAP2K2", "score": 0.99, "pathway": "MAPK_signaling"},
        {"partner": "RAF1", "score": 0.90, "pathway": "MAPK_signaling"},
    ],
}

# ---------------------------------------------------------------------------
# Gene-level PPI scores (pre-computed)
# ---------------------------------------------------------------------------
GENE_PPI_SCORES: dict[str, float] = {}
for _gene, _interactions in PANCREATIC_CANCER_PPI.items():
    if _interactions:
        avg_score = sum(i["score"] for i in _interactions) / len(_interactions)
        GENE_PPI_SCORES[_gene] = avg_score
    else:
        GENE_PPI_SCORES[_gene] = 0.5


# ---------------------------------------------------------------------------
# CancerPPIScorer class
# ---------------------------------------------------------------------------
class CancerPPIScorer:
    """
    Scores genes by their protein-protein interaction network relevance
    to pancreatic cancer.

    Uses curated PPI data focusing on pancreatic cancer driver pathways.
    """

    def __init__(self, cancer_type: str = "pancreatic_ductal_adenocarcinoma"):
        self.cancer_type = cancer_type
        self.ppi_db = PANCREATIC_CANCER_PPI
        self.gene_scores = GENE_PPI_SCORES

    def compute_ppi_score(self, gene: str) -> float:
        """
        Compute PPI network score for a single gene.

        The score reflects:
        - How many pancreatic cancer driver genes it interacts with
        - The confidence of those interactions
        - The number of independent pathways connected
        """
        if gene not in self.ppi_db:
            # Check if gene is an interaction partner of a known driver
            partner_count = 0
            partner_total_confidence = 0.0
            for driver, interactions in self.ppi_db.items():
                for interaction in interactions:
                    if interaction["partner"] == gene:
                        partner_count += 1
                        partner_total_confidence += interaction["score"]

            if partner_count > 0:
                avg_conf = partner_total_confidence / partner_count
                return min(0.85, 0.3 + avg_conf * 0.5)
            return 0.05

        interactions = self.ppi_db[gene]
        avg_confidence = sum(i["score"] for i in interactions) / len(interactions)
        pathway_count = len(set(i["pathway"] for i in interactions))

        # Score formula: confidence base + pathway diversity bonus
        score = avg_confidence * 0.7 + min(pathway_count / 5.0, 1.0) * 0.3
        return min(1.0, score)

    def compute_ppi_score_batch(self, genes: pd.Series) -> pd.Series:
        """Compute PPI scores for a series of genes."""
        return genes.apply(self.compute_ppi_score)

    def score_interaction_network(
        self,
        gene_list: list[str],
    ) -> pd.DataFrame:
        """
        Score the full PPI network for a list of genes.

        Returns a DataFrame with genes, their PPI scores, and interaction
        details.
        """
        rows: list[dict[str, Any]] = []
        for gene in gene_list:
            score = self.compute_ppi_score(gene)
            interactions = self.ppi_db.get(gene, [])
            partner_list = [i["partner"] for i in interactions]
            pathway_list = list(set(i["pathway"] for i in interactions))

            rows.append({
                "gene": gene,
                "ppi_score": score,
                "interaction_count": len(interactions),
                "interaction_partners": ";".join(partner_list),
                "pathways_connected": ";".join(pathway_list),
                "is_driver_hub": score >= 0.80,
            })

        df = pd.DataFrame(rows)
        return df.sort_values("ppi_score", ascending=False).reset_index(drop=True)

    def run(
        self,
        vep_df: pd.DataFrame,
        gene_df: pd.DataFrame | None = None,
        hpo_ids: list[str] | None = None,
    ) -> dict[str, pd.DataFrame]:
        """
        Run PPI scoring on annotated variant and gene-phenotype data.

        Parameters
        ----------
        vep_df : pd.DataFrame
            VEP-annotated variant DataFrame.
        gene_df : pd.DataFrame, optional
            Gene-level phenotype scores.
        hpo_ids : list[str], optional
            HPO term IDs for phenotype filtering.

        Returns
        -------
        dict
            {'ppi_scores': DataFrame, 'ppi_network': DataFrame}
        """
        logger.info("Running PPI scoring on %d variants", len(vep_df))

        # Collect all unique genes
        all_genes = set()
        if "SYMBOL" in vep_df.columns:
            all_genes.update(vep_df["SYMBOL"].dropna().unique())
        if gene_df is not None and "gene" in gene_df.columns:
            all_genes.update(gene_df["gene"].dropna().unique())

        gene_list = sorted(all_genes)

        # Score each gene
        ppi_df = self.score_interaction_network(gene_list)

        # Build variant-level PPI scores
        if "SYMBOL" in vep_df.columns:
            vep_df = vep_df.copy()
            vep_df["ppi_score"] = vep_df["SYMBOL"].map(
                lambda g: self.compute_ppi_score(str(g))
            ).fillna(0.0)
        else:
            vep_df = vep_df.copy()
            vep_df["ppi_score"] = 0.0

        logger.info(
            "PPI scoring complete: %d genes scored (top: %.4f)",
            len(ppi_df),
            ppi_df["ppi_score"].max() if len(ppi_df) > 0 else 0.0,
        )

        return {
            "ppi_scores": vep_df,
            "ppi_network": ppi_df,
        }
