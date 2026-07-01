"""
Data I/O utilities for the Variant Rank module.

Supports reading variants from CSV/VCF formats (via pandas, polars, duckdb),
writing ranked output, and merging external score data.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def read_variants(
    path: str,
    engine: str = "pandas",
) -> pd.DataFrame:
    """
    Read variant data from a CSV file.

    Parameters
    ----------
    path : str
        Path to the variant CSV file (should be VEP-annotated output).
    engine : str
        Backend engine: "pandas", "polars", or "duckdb". Defaults to "pandas".

    Returns
    -------
    pd.DataFrame
        DataFrame of variants.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Variant file not found: {path}")

    logger.info("Reading variants from %s (engine=%s)", path, engine)

    if engine == "polars":
        try:
            import polars as pl
            df = pl.read_csv(path)
            return df.to_pandas()
        except ImportError:
            logger.warning("Polars not available; falling back to pandas")

    elif engine == "duckdb":
        try:
            import duckdb
            con = duckdb.connect()
            df = con.execute(f"SELECT * FROM read_csv_auto('{path}')").fetchdf()
            con.close()
            return df
        except ImportError:
            logger.warning("DuckDB not available; falling back to pandas")

    # Default: pandas
    try:
        df = pd.read_csv(path, low_memory=False)
    except Exception as exc:
        raise ValueError(f"Failed to read variant file: {exc}") from exc

    logger.info("Read %d variants", len(df))
    return df


def write_ranked(df: pd.DataFrame, path: str) -> str:
    """
    Write ranked variants to a CSV file.

    Parameters
    ----------
    df : pd.DataFrame
        Ranked variant DataFrame (must include 'rank' and 'total_score' columns).
    path : str
        Output file path.

    Returns
    -------
    str
        The output file path.
    """
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Select output columns: key fields + score columns, sorted by rank
    key_cols = ["rank", "total_score", "tier"]
    score_cols = [c for c in df.columns if c.startswith("score_")]
    data_cols = [
        "Uploaded_variation", "Location", "Gene", "SYMBOL", "Consequence",
        "IMPACT", "HGVSp", "HGVSc", "CLIN_SIG", "AF",
        "cosmic_id", "tcga_paad_freq", "oncokb_level",
        "is_cancer_hotspot", "is_driver_gene", "is_pancreatic_cancer_gene",
        "cancer_pathway",
    ]

    # Build final column list, keeping only columns that exist
    cols_to_write: list[str] = []
    for col in key_cols + data_cols + score_cols:
        if col in df.columns:
            cols_to_write.append(col)

    # Also include any remaining column not in our lists
    for col in df.columns:
        if col not in cols_to_write:
            cols_to_write.append(col)

    df_out = df[cols_to_write].copy()

    # Ensure rank is integer
    if "rank" in df_out.columns:
        df_out["rank"] = df_out["rank"].astype(int)

    df_out.to_csv(output_path, index=False)
    logger.info("Wrote %d ranked variants to %s", len(df_out), output_path)

    return str(output_path)


def merge_scores(
    vep_df: pd.DataFrame,
    gene_df: pd.DataFrame | None = None,
    ppi_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Merge external gene-level and PPI scores into the variant DataFrame.

    Parameters
    ----------
    vep_df : pd.DataFrame
        VEP-annotated variant DataFrame. Must have a 'SYMBOL' column.
    gene_df : pd.DataFrame, optional
        Gene-level phenotype scores. Must have 'gene' and 'score' columns.
    ppi_df : pd.DataFrame, optional
        PPI network scores. Must have 'gene' and 'ppi_score' columns.

    Returns
    -------
    pd.DataFrame
        Merged DataFrame with added score columns.
    """
    df = vep_df.copy()

    if gene_df is not None and not gene_df.empty:
        if "gene" in gene_df.columns and "score" in gene_df.columns:
            gene_map = dict(zip(gene_df["gene"], gene_df["score"]))
            df["gene_phenotype_score"] = df["SYMBOL"].map(gene_map).fillna(0.0)
            logger.info("Merged gene phenotype scores for %d genes", len(gene_map))
        else:
            logger.warning("Gene score DataFrame missing 'gene' or 'score' columns")

    if ppi_df is not None and not ppi_df.empty:
        if "gene" in ppi_df.columns and "ppi_score" in ppi_df.columns:
            ppi_map = dict(zip(ppi_df["gene"], ppi_df["ppi_score"]))
            df["ppi_network_score"] = df["SYMBOL"].map(ppi_map).fillna(0.0)
            logger.info("Merged PPI scores for %d genes", len(ppi_map))
        else:
            logger.warning("PPI score DataFrame missing 'gene' or 'ppi_score' columns")

    return df
