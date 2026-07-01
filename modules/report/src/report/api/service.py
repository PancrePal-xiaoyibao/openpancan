"""
Core report generation service.

Generates comprehensive pancreatic cancer genomic analysis reports
in Markdown format with SSE streaming for real-time progress updates.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator

import pandas as pd

from report.api.schemas import ReportRequest, SSEEvent
from report.report.drug_recommendations import (
    format_drug_recommendations_md,
    get_drug_recommendations,
)
from report.report.clinical_trials import (
    format_trials_md,
    match_clinical_trials,
)

logger = logging.getLogger(__name__)


class ReportGenerationService:
    """
    Generates pancreatic cancer genomic reports.

    Reads ranked variant data, phenotype scores, PPI scores, and clinical
    text, then produces a comprehensive Markdown report with drug
    recommendations and clinical trial matches. Yields SSE events for
    real-time streaming.
    """

    def __init__(self):
        self.output_dir = Path(os.getenv("REPORT_OUTPUT_DIR", "/tmp/openpancan_reports"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_report(
        self,
        request: ReportRequest,
    ) -> AsyncGenerator[str, None]:
        """
        Generate the report as a stream of SSE-formatted events.

        Yields
        ------
        str
            SSE event lines ("data:{...}\n\n").
        """
        run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
        md_lines: list[str] = []

        try:
            # --- Phase 1: Loading Data ---
            yield self._sse(SSEEvent(
                type="phase", phase="loading",
                content="Loading variant and phenotype data...",
                run_id=run_id, progress=0.05,
            ))

            variants_df = self._load_variants(request.wide_path)
            gene_df = self._load_optional_csv(request.phenotype_path)
            ppi_df = self._load_optional_csv(request.ppi_path)
            hpo_ids = self._load_hpo_ids(request.hpo_path)
            top_n = min(request.top_n, len(variants_df))

            yield self._sse(SSEEvent(
                type="phase", phase="loading",
                content=f"Loaded {len(variants_df)} variants, {len(gene_df) if gene_df is not None else 0} gene scores.",
                run_id=run_id, progress=0.10,
            ))
            await asyncio.sleep(0.1)

            # --- Header ---
            header_md = self._generate_header(request, len(variants_df), top_n)
            md_lines.append(header_md)
            yield self._sse(SSEEvent(type="md", content=header_md, run_id=run_id, progress=0.15))

            # --- Phase 2: Clinical Summary ---
            yield self._sse(SSEEvent(
                type="phase", phase="clinical_summary",
                content="Generating clinical summary...",
                run_id=run_id, progress=0.20,
            ))

            if request.symptom_text:
                summary_md = self._generate_clinical_summary(request.symptom_text)
                md_lines.append(summary_md)
                yield self._sse(SSEEvent(type="md", content=summary_md, run_id=run_id, progress=0.25))

            # --- Phase 3: Top Variants ---
            yield self._sse(SSEEvent(
                type="phase", phase="variants",
                content="Analyzing top variants...",
                run_id=run_id, progress=0.30,
            ))
            await asyncio.sleep(0.1)

            variants_md = self._generate_top_variants_section(variants_df, top_n)
            md_lines.append(variants_md)
            yield self._sse(SSEEvent(type="md", content=variants_md, run_id=run_id, progress=0.45))

            # --- Phase 4: Variant Detail ---
            yield self._sse(SSEEvent(
                type="phase", phase="variant_detail",
                content="Generating variant detail table...",
                run_id=run_id, progress=0.50,
            ))
            await asyncio.sleep(0.1)

            detail_md = self._generate_variant_detail(variants_df, top_n)
            md_lines.append(detail_md)
            yield self._sse(SSEEvent(type="md", content=detail_md, run_id=run_id, progress=0.65))

            # --- Phase 5: Drug Recommendations ---
            yield self._sse(SSEEvent(
                type="phase", phase="drug_recommendations",
                content="Generating drug recommendations...",
                run_id=run_id, progress=0.70,
            ))
            await asyncio.sleep(0.1)

            drug_recs = get_drug_recommendations(variants_df, request.cancer_type)
            drug_md = format_drug_recommendations_md(drug_recs)
            md_lines.append(drug_md)
            yield self._sse(SSEEvent(type="md", content=drug_md, run_id=run_id, progress=0.80))

            # --- Phase 6: Clinical Trials ---
            yield self._sse(SSEEvent(
                type="phase", phase="clinical_trials",
                content="Matching clinical trials...",
                run_id=run_id, progress=0.85,
            ))
            await asyncio.sleep(0.1)

            trials = match_clinical_trials(variants_df, request.cancer_type)
            trials_md = format_trials_md(trials)
            md_lines.append(trials_md)
            yield self._sse(SSEEvent(type="md", content=trials_md, run_id=run_id, progress=0.92))

            # --- Phase 7: Gene & PPI Scores ---
            yield self._sse(SSEEvent(
                type="phase", phase="gene_scores",
                content="Adding gene-level and PPI scores...",
                run_id=run_id, progress=0.95,
            ))

            if gene_df is not None or ppi_df is not None:
                scores_md = self._generate_gene_scores_section(gene_df, ppi_df)
                md_lines.append(scores_md)
                yield self._sse(SSEEvent(type="md", content=scores_md, run_id=run_id, progress=0.97))

            # --- Save Report ---
            report_md_path = self.output_dir / f"{run_id}_report.md"
            report_content = "\n".join(md_lines)
            report_md_path.write_text(report_content)

            # --- Done ---
            yield self._sse(SSEEvent(
                type="done",
                content="Report generation complete.",
                run_id=run_id,
                progress=1.0,
                pdf_url=f"/report/{run_id}/download/report.md",
            ))

            # Store for later download
            self._store_report(run_id, report_content)

        except Exception as exc:
            logger.exception("Report generation failed for %s", run_id)
            yield self._sse(SSEEvent(
                type="error",
                error=str(exc),
                run_id=run_id,
                progress=0.0,
            ))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sse(self, event: SSEEvent) -> str:
        """Serialize an SSEEvent to SSE line format."""
        return f"data:{event.model_dump_json()}\n\n"

    def _load_variants(self, path: str) -> pd.DataFrame:
        """Load variant data CSV."""
        if not path:
            return pd.DataFrame()
        p = Path(path)
        if not p.exists():
            logger.warning("Variant file not found: %s", path)
            return pd.DataFrame()
        return pd.read_csv(path, low_memory=False)

    def _load_optional_csv(self, path: str | None) -> pd.DataFrame | None:
        """Load an optional CSV file."""
        if not path:
            return None
        p = Path(path)
        if not p.exists():
            logger.warning("Optional file not found: %s", path)
            return None
        return pd.read_csv(path)

    def _load_hpo_ids(self, path: str | None) -> list[str]:
        """Load HPO IDs from file."""
        if not path:
            return []
        p = Path(path)
        if not p.exists():
            return []
        with open(path) as f:
            return [line.strip() for line in f if line.strip()]

    def _store_report(self, run_id: str, content: str) -> None:
        """Store report content for later retrieval."""
        # In-memory store (could be file-based or Redis in production)
        if not hasattr(self, "_report_store"):
            self._report_store: dict[str, str] = {}
        self._report_store[run_id] = content

    def get_report(self, run_id: str) -> str | None:
        """Retrieve a stored report by run ID."""
        store = getattr(self, "_report_store", {})
        return store.get(run_id)

    # ------------------------------------------------------------------
    # Report section generators
    # ------------------------------------------------------------------

    def _generate_header(self, request: ReportRequest, n_variants: int, top_n: int) -> str:
        """Generate the report header."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        cancer_name = request.cancer_type.replace("_", " ").title()
        return (
            f"# OpenPanCan Genomic Analysis Report\n\n"
            f"**Cancer Type**: {cancer_name}\n\n"
            f"**Date**: {now}\n\n"
            f"**Variants Analyzed**: {n_variants}\n\n"
            f"**Top Variants Featured**: {top_n}\n\n"
            f"---\n\n"
        )

    def _generate_clinical_summary(self, symptom_text: str) -> str:
        """Generate clinical presentation summary section."""
        max_len = 500
        summary = symptom_text[:max_len] + ("..." if len(symptom_text) > max_len else "")
        return (
            f"## Clinical Presentation\n\n"
            f"{summary}\n\n"
            f"---\n\n"
        )

    def _generate_top_variants_section(self, df: pd.DataFrame, top_n: int) -> str:
        """Generate the top variants summary section."""
        if df.empty:
            return "## Top Variants\n\nNo variants available for analysis.\n\n---\n\n"

        lines = [
            "## Top Cancer Driver Variant Candidates\n\n",
            f"The top {top_n} variants ranked by cancer driver potential:\n\n",
        ]

        # Determine ranking columns
        if "rank" in df.columns:
            df_sorted = df.sort_values("rank").head(top_n)
        elif "total_score" in df.columns:
            df_sorted = df.sort_values("total_score", ascending=False).head(top_n)
        elif "phenotype_score" in df.columns:
            df_sorted = df.sort_values("phenotype_score", ascending=False).head(top_n)
        else:
            df_sorted = df.head(top_n)

        for i, (_, row) in enumerate(df_sorted.iterrows(), 1):
            gene = row.get("SYMBOL", row.get("Gene", "Unknown"))
            hgvsp = row.get("HGVSp", "N/A")
            consequence = row.get("Consequence", "N/A")
            impact = row.get("IMPACT", "N/A")

            total_score = None
            for sc in ["total_score", "phenotype_score"]:
                if sc in row.index and pd.notna(row[sc]):
                    total_score = float(row[sc])
                    break

            lines.append(f"### {i}. {gene} {hgvsp}\n")
            lines.append(f"- **Consequence**: {consequence}")
            lines.append(f"- **Impact**: {impact}")
            if total_score is not None:
                lines.append(f"- **Score**: {total_score:.4f}")

            # Add cancer annotations
            for field, label in [
                ("is_cancer_hotspot", "Cancer Hotspot"),
                ("is_driver_gene", "Driver Gene"),
                ("is_pancreatic_cancer_gene", "Pancreatic Cancer Gene"),
                ("cosmic_id", "COSMIC ID"),
                ("tcga_paad_freq", "TCGA PAAD Freq"),
                ("cancer_pathway", "Pathway"),
            ]:
                if field in row.index and pd.notna(row[field]) and str(row[field]) not in ("", "nan", "None", "0", "0.0", "False"):
                    val = row[field]
                    if field == "tcga_paad_freq":
                        try:
                            val = f"{float(val):.3f}"
                        except (ValueError, TypeError):
                            pass
                    lines.append(f"- **{label}**: {val}")

            lines.append("")

        lines.append("---\n")
        return "\n".join(lines)

    def _generate_variant_detail(self, df: pd.DataFrame, top_n: int) -> str:
        """Generate detailed variant table."""
        if df.empty:
            return ""

        lines = [
            "## Variant Detail Table\n\n",
            "Complete annotation for top-ranked variants:\n\n",
        ]

        # Select columns for the table
        table_cols = [
            "rank", "SYMBOL", "HGVSp", "Consequence", "IMPACT",
            "AF", "CLIN_SIG", "total_score", "cosmic_id",
            "tcga_paad_freq", "oncokb_level", "is_cancer_hotspot",
            "cancer_pathway",
        ]
        available_cols = [c for c in table_cols if c in df.columns]

        if "rank" in df.columns:
            df_display = df.sort_values("rank").head(top_n)
        elif "total_score" in df.columns:
            df_display = df.sort_values("total_score", ascending=False).head(top_n)
        else:
            df_display = df.head(top_n)

        subset = df_display[available_cols]

        # Build markdown table
        header = "| " + " | ".join(available_cols) + " |"
        separator = "|" + "|".join(["---" for _ in available_cols]) + "|"
        lines.append(header)
        lines.append(separator)

        for _, row in subset.iterrows():
            cells = []
            for col in available_cols:
                val = row[col]
                if pd.isna(val):
                    cells.append("")
                elif isinstance(val, float):
                    cells.append(f"{val:.4f}")
                else:
                    cells.append(str(val))
            lines.append("| " + " | ".join(cells) + " |")

        lines.append("\n---\n")
        return "\n".join(lines)

    def _generate_gene_scores_section(
        self,
        gene_df: pd.DataFrame | None,
        ppi_df: pd.DataFrame | None,
    ) -> str:
        """Generate gene-level and PPI scores summary."""
        lines = ["## Gene-Level Scores\n\n"]

        if gene_df is not None and not gene_df.empty:
            lines.append("### Phenotype Scores\n\n")
            if "phenotype_score" in gene_df.columns:
                top = gene_df.sort_values("phenotype_score", ascending=False).head(10)
                for _, row in top.iterrows():
                    gene = row.get("gene", "Unknown")
                    score = row.get("phenotype_score", 0)
                    lines.append(f"- **{gene}**: {float(score):.4f}")
                lines.append("")

        if ppi_df is not None and not ppi_df.empty:
            lines.append("### PPI Network Scores\n\n")
            if "ppi_score" in ppi_df.columns:
                top = ppi_df.sort_values("ppi_score", ascending=False).head(10)
                for _, row in top.iterrows():
                    gene = row.get("gene", "Unknown")
                    score = row.get("ppi_score", 0)
                    hub = " ⭐ hub" if row.get("is_driver_hub", False) else ""
                    lines.append(f"- **{gene}**: {float(score):.4f}{hub}")
                lines.append("")

        lines.append("---\n")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
report_service = ReportGenerationService()
