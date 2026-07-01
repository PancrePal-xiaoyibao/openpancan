"""SQLAlchemy ORM models for pancreatic cancer patient management."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CancerPatient(Base):
    """Pancreatic cancer patient clinical record."""

    __tablename__ = "cancer_patients"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = Column(String(255), nullable=False)
    age: Mapped[int | None] = Column(Integer, nullable=True)
    sex: Mapped[str | None] = Column(String(20), nullable=True)  # Male / Female / Unknown
    ethnicity: Mapped[str | None] = Column(String(100), nullable=True)
    diagnosis: Mapped[str | None] = Column(String(500), nullable=True)
    tumor_location: Mapped[str | None] = Column(
        String(50), nullable=True
    )  # head / body / tail / uncinate / unknown
    tumor_stage: Mapped[str | None] = Column(
        String(20), nullable=True
    )  # I / II / III / IV
    tumor_grade: Mapped[str | None] = Column(
        String(10), nullable=True
    )  # G1 / G2 / G3 / G4
    histology_type: Mapped[str | None] = Column(String(200), nullable=True)
    ca19_9_level: Mapped[float | None] = Column(Float, nullable=True)

    # JSON columns for structured data
    biomarkers: Mapped[dict[str, Any] | None] = Column(JSON, nullable=True, default=dict)
    # Example: {"KRAS": "mutated", "TP53": "wild_type", "SMAD4": "unknown", ...}

    treatment_history: Mapped[list[dict[str, Any]] | None] = Column(
        JSON, nullable=True, default=list
    )
    # Example: [{"type": "surgery", "drug": "Whipple", "date": "2024-01-15", "response": "PR"}]

    hpo_terms: Mapped[list[dict[str, Any]] | None] = Column(
        JSON, nullable=True, default=list
    )
    # Example: [{"hpo_id": "HP:0002664", "hpo_term": "Neoplasm", "confidence": 0.9}]

    family_history: Mapped[str | None] = Column(Text, nullable=True)
    smoking_status: Mapped[str | None] = Column(String(50), nullable=True)
    alcohol_history: Mapped[str | None] = Column(String(100), nullable=True)

    created_at: Mapped[datetime] = Column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    # Relationships
    somatic_variants = relationship("SomaticVariant", back_populates="patient", cascade="all, delete-orphan")
    germline_variants = relationship("GermlineVariant", back_populates="patient", cascade="all, delete-orphan")
    treatment_records = relationship("TreatmentRecord", back_populates="patient", cascade="all, delete-orphan")
    clinical_reports = relationship("ClinicalReport", back_populates="patient", cascade="all, delete-orphan")
    vep_jobs = relationship("VEPJob", back_populates="patient", cascade="all, delete-orphan")


class SomaticVariant(Base):
    """Tumor somatic variant detected by sequencing."""

    __tablename__ = "somatic_variants"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True, index=True)
    patient_id: Mapped[int] = Column(
        Integer, ForeignKey("cancer_patients.id", ondelete="CASCADE"), nullable=False, index=True
    )

    chromosome: Mapped[str] = Column(String(10), nullable=False)
    position: Mapped[int] = Column(Integer, nullable=False)
    ref: Mapped[str] = Column(String(500), nullable=False)
    alt: Mapped[str] = Column(String(500), nullable=False)
    gene: Mapped[str | None] = Column(String(50), nullable=True, index=True)
    variant_type: Mapped[str] = Column(
        String(10), nullable=False
    )  # SNV / INDEL / CNV / SV
    vaf: Mapped[float | None] = Column(Float, nullable=True)  # Variant Allele Frequency
    tumor_depth: Mapped[int | None] = Column(Integer, nullable=True)
    normal_depth: Mapped[int | None] = Column(Integer, nullable=True)
    cosmic_id: Mapped[str | None] = Column(String(50), nullable=True)
    oncokb_level: Mapped[str | None] = Column(
        String(10), nullable=True
    )  # 1 / 2 / 3A / 3B / 4
    is_cancer_hotspot: Mapped[bool] = Column(Integer, default=0)  # SQLite bool stored as int
    driver_prediction: Mapped[str | None] = Column(String(50), nullable=True)
    consequence: Mapped[str | None] = Column(String(200), nullable=True)
    impact: Mapped[str | None] = Column(String(50), nullable=True)  # HIGH / MODERATE / LOW / MODIFIER
    hgvs_c: Mapped[str | None] = Column(String(200), nullable=True)
    hgvs_p: Mapped[str | None] = Column(String(200), nullable=True)
    clinvar_significance: Mapped[str | None] = Column(String(200), nullable=True)
    revel_score: Mapped[float | None] = Column(Float, nullable=True)
    cadd_score: Mapped[float | None] = Column(Float, nullable=True)
    spliceai_score: Mapped[float | None] = Column(Float, nullable=True)
    gnomad_af: Mapped[float | None] = Column(Float, nullable=True)
    strand_bias: Mapped[float | None] = Column(Float, nullable=True)
    copy_number: Mapped[float | None] = Column(Float, nullable=True)  # For CNV
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    patient = relationship("CancerPatient", back_populates="somatic_variants")
    amp_asco_cap_tiers = relationship("AMPASCOCAPTier", back_populates="somatic_variant", cascade="all, delete-orphan")


class GermlineVariant(Base):
    """Germline (inherited) variant detected by sequencing."""

    __tablename__ = "germline_variants"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True, index=True)
    patient_id: Mapped[int] = Column(
        Integer, ForeignKey("cancer_patients.id", ondelete="CASCADE"), nullable=False, index=True
    )

    chromosome: Mapped[str] = Column(String(10), nullable=False)
    position: Mapped[int] = Column(Integer, nullable=False)
    ref: Mapped[str] = Column(String(500), nullable=False)
    alt: Mapped[str] = Column(String(500), nullable=False)
    gene: Mapped[str | None] = Column(String(50), nullable=True, index=True)
    variant_type: Mapped[str] = Column(
        String(10), nullable=False
    )  # SNV / INDEL / CNV / SV
    consequence: Mapped[str | None] = Column(String(200), nullable=True)
    impact: Mapped[str | None] = Column(String(50), nullable=True)
    hgvs_c: Mapped[str | None] = Column(String(200), nullable=True)
    hgvs_p: Mapped[str | None] = Column(String(200), nullable=True)
    clinvar_significance: Mapped[str | None] = Column(String(200), nullable=True)
    gnomad_af: Mapped[float | None] = Column(Float, nullable=True)
    revel_score: Mapped[float | None] = Column(Float, nullable=True)
    cadd_score: Mapped[float | None] = Column(Float, nullable=True)
    spliceai_score: Mapped[float | None] = Column(Float, nullable=True)
    acmg_classification: Mapped[str | None] = Column(
        String(50), nullable=True
    )  # Pathogenic / Likely Pathogenic / VUS / Likely Benign / Benign
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    patient = relationship("CancerPatient", back_populates="germline_variants")
    acmg_evidence = relationship("ACMGEvidence", back_populates="germline_variant", cascade="all, delete-orphan")


class ACMGEvidence(Base):
    """ACMG criteria evidence for germline variant classification."""

    __tablename__ = "acmg_evidence"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True, index=True)
    germline_variant_id: Mapped[int] = Column(
        Integer,
        ForeignKey("germline_variants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    criterion: Mapped[str] = Column(
        String(10), nullable=False
    )  # PVS1 / PS1-PS4 / PM1-PM6 / PP1-PP5 / BA1 / BS1-BS4 / BP1-BP7
    evidence_level: Mapped[str | None] = Column(
        String(20), nullable=True
    )  # Very Strong / Strong / Moderate / Supporting / Stand-alone
    description: Mapped[str | None] = Column(Text, nullable=True)
    evidence_source: Mapped[str | None] = Column(String(200), nullable=True)
    is_applied: Mapped[bool] = Column(Integer, default=1)

    # Relationships
    germline_variant = relationship("GermlineVariant", back_populates="acmg_evidence")


class AMPASCOCAPTier(Base):
    """AMP/ASCO/CAP tier classification for somatic variants."""

    __tablename__ = "amp_asco_cap_tiers"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True, index=True)
    somatic_variant_id: Mapped[int] = Column(
        Integer,
        ForeignKey("somatic_variants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    tier: Mapped[str] = Column(
        String(5), nullable=False, index=True
    )  # I / II / III / IV
    evidence_category: Mapped[str | None] = Column(String(200), nullable=True)
    clinical_significance: Mapped[str | None] = Column(Text, nullable=True)
    biomarker_relevance: Mapped[str | None] = Column(Text, nullable=True)
    therapeutic_relevance: Mapped[str | None] = Column(Text, nullable=True)
    confidence: Mapped[str | None] = Column(String(50), nullable=True)  # High / Medium / Low
    notes: Mapped[str | None] = Column(Text, nullable=True)

    # Relationships
    somatic_variant = relationship("SomaticVariant", back_populates="amp_asco_cap_tiers")


class TreatmentRecord(Base):
    """Patient treatment record."""

    __tablename__ = "treatment_records"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True, index=True)
    patient_id: Mapped[int] = Column(
        Integer, ForeignKey("cancer_patients.id", ondelete="CASCADE"), nullable=False, index=True
    )

    treatment_type: Mapped[str] = Column(
        String(50), nullable=False
    )  # surgery / chemotherapy / radiation / targeted_therapy / immunotherapy
    drug_name: Mapped[str | None] = Column(String(200), nullable=True)
    regimen: Mapped[str | None] = Column(String(500), nullable=True)
    start_date: Mapped[str | None] = Column(String(30), nullable=True)
    end_date: Mapped[str | None] = Column(String(30), nullable=True)
    response: Mapped[str | None] = Column(
        String(10), nullable=True
    )  # CR / PR / SD / PD
    notes: Mapped[str | None] = Column(Text, nullable=True)

    # Relationships
    patient = relationship("CancerPatient", back_populates="treatment_records")


class ClinicalReport(Base):
    """Generated clinical report record."""

    __tablename__ = "clinical_reports"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True, index=True)
    patient_id: Mapped[int] = Column(
        Integer, ForeignKey("cancer_patients.id", ondelete="CASCADE"), nullable=False, index=True
    )

    report_type: Mapped[str] = Column(
        String(50), nullable=False
    )  # genomic / clinical / comprehensive
    run_id: Mapped[str | None] = Column(String(100), nullable=True)
    markdown_path: Mapped[str | None] = Column(String(500), nullable=True)
    pdf_path: Mapped[str | None] = Column(String(500), nullable=True)
    summary: Mapped[str | None] = Column(Text, nullable=True)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    patient = relationship("CancerPatient", back_populates="clinical_reports")


class VEPJob(Base):
    """VEP annotation job tracking."""

    __tablename__ = "vep_jobs"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True, index=True)
    patient_id: Mapped[int] = Column(
        Integer, ForeignKey("cancer_patients.id", ondelete="CASCADE"), nullable=False, index=True
    )

    job_id: Mapped[str] = Column(String(100), nullable=False, index=True)
    status: Mapped[str] = Column(
        String(20), nullable=False, default="queued"
    )  # queued / running / completed / failed
    vcf_path: Mapped[str | None] = Column(String(500), nullable=True)
    output_csv_path: Mapped[str | None] = Column(String(500), nullable=True)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    patient = relationship("CancerPatient", back_populates="vep_jobs")
