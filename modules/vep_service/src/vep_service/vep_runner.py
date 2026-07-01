"""
Background VCF processing for the VEP (Variant Effect Predictor) service.

Provides process_vcf_job() that parses a VCF file, applies simulated VEP
annotation and cancer-specific enrichment, and produces a structured annotated
CSV with standard VEP columns plus cancer-specific columns.
"""

from __future__ import annotations

import csv
import io
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from vep_service.cancer_annotation import (
    PANCREATIC_CANCER_DRIVER_GENES,
    KRAS_HOTSPOT_MUTATIONS,
    TCGA_PAAD_FREQUENCIES,
    add_cancer_annotations,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Standard VEP output columns (simulated)
# ---------------------------------------------------------------------------
VEP_OUTPUT_COLUMNS: list[str] = [
    "Uploaded_variation",
    "Location",
    "Allele",
    "Gene",
    "Feature",
    "Feature_type",
    "Consequence",
    "cDNA_position",
    "CDS_position",
    "Protein_position",
    "Amino_acids",
    "Codons",
    "Existing_variation",
    "IMPACT",
    "DISTANCE",
    "STRAND",
    "FLAGS",
    "SYMBOL",
    "SYMBOL_SOURCE",
    "HGNC_ID",
    "BIOTYPE",
    "CANONICAL",
    "MANE_SELECT",
    "MANE_PLUS_CLINICAL",
    "SIFT",
    "PolyPhen",
    "EXON",
    "INTRON",
    "DOMAINS",
    "AF",
    "gnomADg_AF",
    "gnomADe_AF",
    "MAX_AF",
    "MAX_AF_POPS",
    "CLIN_SIG",
    "SOMATIC",
    "PHENO",
    "PUBMED",
    "HGVSc",
    "HGVSp",
    "HGVS_OFFSET",
]

# Additional cancer columns appended after VEP columns
CANCER_OUTPUT_COLUMNS: list[str] = [
    "cosmic_id",
    "tcga_paad_freq",
    "oncokb_level",
    "is_cancer_hotspot",
    "is_driver_gene",
    "is_pancreatic_cancer_gene",
    "cancer_pathway",
]

# ---------------------------------------------------------------------------
# Consequence ranking (higher = more severe)
# ---------------------------------------------------------------------------
CONSEQUENCE_SEVERITY: dict[str, int] = {
    "transcript_ablation": 10,
    "splice_acceptor_variant": 9,
    "splice_donor_variant": 9,
    "stop_gained": 8,
    "frameshift_variant": 7,
    "stop_lost": 7,
    "start_lost": 6,
    "transcript_amplification": 6,
    "inframe_insertion": 5,
    "inframe_deletion": 5,
    "missense_variant": 4,
    "protein_altering_variant": 4,
    "splice_region_variant": 3,
    "splice_polypyrimidine_tract_variant": 3,
    "incomplete_terminal_codon_variant": 3,
    "start_retained_variant": 3,
    "stop_retained_variant": 3,
    "synonymous_variant": 2,
    "coding_sequence_variant": 2,
    "mature_miRNA_variant": 2,
    "5_prime_UTR_variant": 1,
    "3_prime_UTR_variant": 1,
    "non_coding_transcript_exon_variant": 1,
    "intron_variant": 0,
    "NMD_transcript_variant": 0,
    "non_coding_transcript_variant": 0,
    "upstream_gene_variant": 0,
    "downstream_gene_variant": 0,
    "TFBS_ablation": 1,
    "TFBS_amplification": 1,
    "TF_binding_site_variant": 1,
    "regulatory_region_variant": 0,
    "regulatory_region_ablation": 1,
    "regulatory_region_amplification": 1,
    "feature_elongation": 1,
    "feature_truncation": 1,
    "intergenic_variant": 0,
}


# ---------------------------------------------------------------------------
# Amino acid three-letter to one-letter mapping
# ---------------------------------------------------------------------------
AA_THREE_TO_ONE: dict[str, str] = {
    "Ala": "A", "Arg": "R", "Asn": "N", "Asp": "D",
    "Cys": "C", "Gln": "Q", "Glu": "E", "Gly": "G",
    "His": "H", "Ile": "I", "Leu": "L", "Lys": "K",
    "Met": "M", "Phe": "F", "Pro": "P", "Ser": "S",
    "Thr": "T", "Trp": "W", "Tyr": "Y", "Val": "V",
    "Ter": "*", "Sec": "U", "Pyl": "O",
}


# ---------------------------------------------------------------------------
# VCF Parsing
# ---------------------------------------------------------------------------
def _parse_vcf(vcf_path: str) -> list[dict[str, Any]]:
    """
    Parse a VCF file and extract variant records.

    Returns a list of dicts with keys: CHROM, POS, ID, REF, ALT, QUAL, FILTER, INFO.
    """
    variants: list[dict[str, Any]] = []
    with open(vcf_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("##"):
                continue
            if line.startswith("#"):
                # Header line: #CHROM POS ID REF ALT QUAL FILTER INFO [FORMAT sample...]
                continue
            parts = line.split("\t")
            if len(parts) < 8:
                continue
            variant = {
                "CHROM": parts[0],
                "POS": parts[1],
                "ID": parts[2],
                "REF": parts[3],
                "ALT": parts[4],
                "QUAL": parts[5],
                "FILTER": parts[6],
                "INFO": parts[7],
                "FORMAT": parts[8] if len(parts) > 8 else "",
                "SAMPLE": parts[9] if len(parts) > 9 else "",
            }
            variants.append(variant)
    logger.info("Parsed %d variants from VCF: %s", len(variants), vcf_path)
    return variants


def _parse_info(info_str: str) -> dict[str, str]:
    """Parse the INFO column from a VCF record into a dict."""
    info_dict: dict[str, str] = {}
    for item in info_str.split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            info_dict[key] = value
        elif item:
            info_dict[item] = "True"
    return info_dict


# ---------------------------------------------------------------------------
# Simulated VEP annotation
# ---------------------------------------------------------------------------
def _simulate_vep_annotation(variant: dict[str, Any]) -> dict[str, Any]:
    """
    Simulate VEP annotation for a single variant.

    Produces realistic-looking annotations based on the variant position
    and gene context extracted from INFO. In a real deployment this would
    call the actual VEP tool.
    """
    chrom = variant["CHROM"]
    pos = int(variant["POS"])
    ref = variant["REF"]
    alt = variant["ALT"]
    info = _parse_info(variant["INFO"])

    # Try to extract gene from INFO
    gene = info.get("GENE", info.get("Gene", ""))
    if not gene:
        # Assign a gene based on chromosome (simplified mapping)
        gene = _gene_from_chrom_pos(chrom, pos)

    # Determine variant type
    if len(ref) == 1 and len(alt) == 1:
        var_type = "SNV"
    elif len(ref) > len(alt):
        var_type = "deletion"
    else:
        var_type = "insertion"

    # Determine consequence
    consequence = _determine_consequence(var_type, gene)

    # Generate HGVS notations
    hgvsc, hgvsp = _generate_hgvs(variant, gene, ref, alt)

    # Generate simulated quality metrics
    sift_score = _simulate_sift(gene, hgvsp)
    polyphen_score = _simulate_polyphen(gene, hgvsp)
    impact = _determine_impact(consequence)

    # Allele frequency (simulated)
    af = TCGA_PAAD_FREQUENCIES.get(gene, 0.001)

    # Clinical significance
    clin_sig = _clinical_significance(gene, consequence)

    # Build the full annotation record
    record: dict[str, Any] = {
        "Uploaded_variation": f"{chrom}_{pos}_{ref}/{alt}",
        "Location": f"{chrom}:{pos}",
        "Allele": alt,
        "Gene": gene,
        "Feature": f"ENST{hash(gene + str(pos)) % 1000000000:09d}",
        "Feature_type": "Transcript",
        "Consequence": consequence,
        "cDNA_position": str(pos % 3000),
        "CDS_position": str(pos % 1000),
        "Protein_position": str(max(1, pos % 800)),
        "Amino_acids": _amino_acid_change(ref, alt, var_type),
        "Codons": f"{ref.upper()}gg/{alt.upper()}gg",
        "Existing_variation": f"rs{hash(f'{chrom}_{pos}') % 1000000000}",
        "IMPACT": impact,
        "DISTANCE": "0",
        "STRAND": "1" if pos % 2 == 0 else "-1",
        "FLAGS": "",
        "SYMBOL": gene,
        "SYMBOL_SOURCE": "HGNC",
        "HGNC_ID": f"HGNC:{hash(gene) % 50000}",
        "BIOTYPE": "protein_coding",
        "CANONICAL": "YES",
        "MANE_SELECT": "",
        "MANE_PLUS_CLINICAL": "",
        "SIFT": f"deleterious({sift_score})" if sift_score < 0.05 else f"tolerated({sift_score})",
        "PolyPhen": f"probably_damaging({polyphen_score})" if polyphen_score > 0.85
        else f"possibly_damaging({polyphen_score})" if polyphen_score > 0.5
        else f"benign({polyphen_score})",
        "EXON": f"{pos % 20 + 1}/{(pos % 22) + 1}",
        "INTRON": "",
        "DOMAINS": _get_domains(gene),
        "AF": f"{af:.6f}",
        "gnomADg_AF": f"{af * 0.8:.6f}",
        "gnomADe_AF": f"{af * 0.6:.6f}",
        "MAX_AF": f"{af:.6f}",
        "MAX_AF_POPS": "EAS",
        "CLIN_SIG": clin_sig,
        "SOMATIC": "1" if gene in PANCREATIC_CANCER_DRIVER_GENES else "0",
        "PHENO": "1" if gene in PANCREATIC_CANCER_DRIVER_GENES else "0",
        "PUBMED": str(hash(gene) % 30000000 + 10000000),
        "HGVSc": hgvsc,
        "HGVSp": hgvsp,
        "HGVS_OFFSET": "0",
    }
    return record


def _gene_from_chrom_pos(chrom: str, pos: int) -> str:
    """Very simplified gene assignment based on chromosome and position."""
    chrom_genes: dict[str, list[str]] = {
        "12": ["KRAS", "ERBB3"],
        "17": ["TP53", "BRCA1"],
        "18": ["SMAD4"],
        "9": ["CDKN2A"],
        "13": ["BRCA2"],
        "16": ["PALB2"],
        "11": ["ATM"],
        "1": ["ARID1A"],
        "17": ["RNF43"],
        "19": ["STK11"],
        "3": ["TGFBR2"],
        "17": ["MAP2K4"],
        "7": ["EGFR", "MET"],
        "10": ["PTEN"],
        "3": ["PIK3CA"],
    }
    genes = chrom_genes.get(chrom, ["Unknown"])
    index = pos % len(genes) if genes else 0
    return genes[index]


def _determine_consequence(var_type: str, gene: str) -> str:
    """Determine a realistic consequence based on variant type and gene."""
    if var_type == "SNV":
        if gene in ["KRAS", "TP53", "SMAD4"]:
            return "missense_variant"
        if gene in ["CDKN2A", "BRCA1", "BRCA2"]:
            options = ["missense_variant", "stop_gained", "frameshift_variant"]
            return options[hash(gene) % len(options)]
        return "missense_variant"
    elif var_type == "deletion":
        options = ["frameshift_variant", "inframe_deletion"]
        return options[hash(gene) % 2]
    else:
        return "frameshift_variant"


def _determine_impact(consequence: str) -> str:
    """Map consequence to IMPACT level."""
    if consequence in ("transcript_ablation", "splice_acceptor_variant",
                       "splice_donor_variant", "stop_gained", "frameshift_variant",
                       "stop_lost", "start_lost"):
        return "HIGH"
    elif consequence in ("missense_variant", "inframe_insertion", "inframe_deletion",
                         "protein_altering_variant"):
        return "MODERATE"
    elif consequence in ("synonymous_variant", "splice_region_variant"):
        return "LOW"
    return "MODIFIER"


def _generate_hgvs(variant: dict[str, Any], gene: str,
                   ref: str, alt: str) -> tuple[str, str]:
    """Generate HGVS coding and protein notation."""
    chrom = variant["CHROM"]
    pos = int(variant["POS"])
    aa_ref = _translate_amino_acid(ref)
    aa_alt = _translate_amino_acid(alt)

    # Coding DNA change
    cds_pos = pos % 1000
    hgvsc = f"NM_{hash(gene) % 1000000:06d}.{1 + pos % 5}:c.{cds_pos}{ref}>{alt}"

    # Protein change (simplified)
    prot_pos = max(1, pos % 800)
    if aa_ref and aa_alt:
        hgvsp = f"ENSP{hash(gene + str(pos)) % 10000000:07d}:p.{aa_ref}{prot_pos}{aa_alt}"
    elif len(ref) > len(alt):
        # Deletion
        hgvsp = f"ENSP{hash(gene + str(pos)) % 10000000:07d}:p.{aa_ref}{prot_pos}fs"
    else:
        hgvsp = (f"ENSP{hash(gene + str(pos)) % 10000000:07d}"
                 f":p.{_get_random_aa(pos)}{prot_pos}{_get_random_aa(pos + 1)}")

    return hgvsc, hgvsp


def _translate_amino_acid(ref: str) -> str:
    """Rudimentary: try to map a single-letter ref to corresponding letter (a no-op)."""
    if len(ref) == 1 and ref.isalpha():
        return ref.upper()
    return ""


def _amino_acid_change(ref: str, alt: str, var_type: str) -> str:
    """Generate amino acid change representation."""
    if var_type != "SNV":
        return "X/X"
    aa_ref = ref.upper()
    aa_alt = alt.upper()
    return f"{aa_ref}/{aa_alt}"


def _get_random_aa(seed: int) -> str:
    """Pick a random amino acid letter deterministically."""
    aa_list = list("ACDEFGHIKLMNPQRSTVWY")
    return aa_list[seed % len(aa_list)]


def _simulate_sift(gene: str, hgvsp: str) -> str:
    """Simulate a SIFT score based on gene importance."""
    if gene in ("KRAS", "TP53", "SMAD4", "CDKN2A"):
        return "0.00"
    if gene in PANCREATIC_CANCER_DRIVER_GENES:
        return "0.01"
    return "0.15"


def _simulate_polyphen(gene: str, hgvsp: str) -> str:
    """Simulate a PolyPhen score."""
    if gene in ("KRAS", "TP53", "SMAD4"):
        return "1.000"
    if gene in PANCREATIC_CANCER_DRIVER_GENES:
        return "0.950"
    return "0.300"


def _clinical_significance(gene: str, consequence: str) -> str:
    """Assign a clinical significance string."""
    if gene in ("KRAS", "TP53", "SMAD4", "CDKN2A", "BRCA1", "BRCA2"):
        return "pathogenic"
    if gene in PANCREATIC_CANCER_DRIVER_GENES:
        return "likely_pathogenic"
    if consequence in ("frameshift_variant", "stop_gained"):
        return "pathogenic"
    return "uncertain_significance"


def _get_domains(gene: str) -> str:
    """Return domain annotations for known cancer genes."""
    domains: dict[str, str] = {
        "KRAS": "PROSITE_profiles:PS51422&GTPase_Ras",
        "TP53": "Pfam:PF00870&P53",
        "SMAD4": "Pfam:PF03166&MH2",
        "CDKN2A": "PANTHER:PTHR10693&CDK_inhibitor",
        "BRCA1": "Pfam:PF00097&BRCT",
        "BRCA2": "Pfam:PF09104&BRCA2",
        "ATM": "Pfam:PF00454&PI3_PI4_kinase",
    }
    return domains.get(gene, "")


# ---------------------------------------------------------------------------
# Main job processing function
# ---------------------------------------------------------------------------
def process_vcf_job(
    job_id: str,
    vcf_path: str,
    params: dict[str, Any] | None = None,
) -> str:
    """
    Process a VCF file for a VEP annotation job.

    Parses the VCF, applies simulated VEP annotation, enriches with cancer
    annotations, and writes the output CSV.

    Parameters
    ----------
    job_id : str
        Unique job identifier.
    vcf_path : str
        Path to the input VCF file.
    params : dict, optional
        Additional parameters (hgvs, fork, chromosomes, hpo_ids, etc.).

    Returns
    -------
    str
        Path to the output annotated CSV file.
    """
    if params is None:
        params = {}

    logger.info("Starting VEP job %s for VCF: %s", job_id, vcf_path)

    # Determine output directory
    output_dir = params.get("output_dir", str(Path(vcf_path).parent / "outputs"))
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f"{job_id}.vep_annotated.csv")

    # Parse VCF
    variants = _parse_vcf(vcf_path)
    if not variants:
        logger.warning("No variants found in VCF; writing empty output")
        pd.DataFrame(columns=VEP_OUTPUT_COLUMNS + CANCER_OUTPUT_COLUMNS).to_csv(
            output_path, index=False
        )
        return output_path

    # Annotate each variant
    annotated: list[dict[str, Any]] = []
    for variant in variants:
        annotation = _simulate_vep_annotation(variant)
        annotated.append(annotation)

    # Convert to DataFrame
    df = pd.DataFrame(annotated)

    # Ensure standard VEP columns exist
    for col in VEP_OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    # Sort by IMPACT severity
    impact_order = {"HIGH": 0, "MODERATE": 1, "LOW": 2, "MODIFIER": 3}
    df["_impact_sort"] = df["IMPACT"].map(impact_order).fillna(9)
    df = df.sort_values("_impact_sort").drop(columns=["_impact_sort"])

    # Add cancer annotations
    df = add_cancer_annotations(df)

    # Select final columns
    all_columns = [c for c in VEP_OUTPUT_COLUMNS + CANCER_OUTPUT_COLUMNS if c in df.columns]
    df_out = df[all_columns]

    # Write CSV
    df_out.to_csv(output_path, index=False)

    logger.info(
        "VEP job %s completed: %d variants annotated → %s",
        job_id, len(df_out), output_path,
    )

    return output_path
