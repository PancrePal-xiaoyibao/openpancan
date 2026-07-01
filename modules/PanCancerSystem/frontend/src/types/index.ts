// =============================================================================
// OpenPanCan - TypeScript Type Definitions
// =============================================================================

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

export type Gender = 'male' | 'female' | 'other' | 'unknown';

export type VariantType = 'somatic' | 'germline';

export type ACMGTier = 'I' | 'II' | 'III' | 'IV';

export type AMPASCOCAPLevel = 'A' | 'B' | 'C' | 'D';

export type ReportStatus = 'draft' | 'generating' | 'completed' | 'failed';

export type TreatmentStatus = 'ongoing' | 'completed' | 'discontinued' | 'planned';

export type BiomarkerStatus = 'positive' | 'negative' | 'unknown' | 'pending';

// ---------------------------------------------------------------------------
// Cancer Patient
// ---------------------------------------------------------------------------

export interface CancerPatient {
  id: string;
  patient_code: string;
  age: number | null;
  gender: Gender;
  diagnosis: string;
  diagnosis_date: string | null;
  cancer_type: string;
  stage: string | null;
  tumor_site: string;
  histological_type: string | null;
  grade: string | null;
  smoking_history: string | null;
  family_history: string | null;
  ecog_score: number | null;
  survival_status: string;
  created_at: string;
  updated_at: string;

  // Relations
  variants?: SomaticVariant[];
  germline_variants?: GermlineVariant[];
  treatments?: TreatmentRecord[];
  reports?: ClinicalReport[];
}

export interface PatientCreate {
  patient_code: string;
  age?: number;
  gender?: Gender;
  diagnosis: string;
  diagnosis_date?: string;
  cancer_type?: string;
  stage?: string;
  tumor_site?: string;
  histological_type?: string;
  grade?: string;
  smoking_history?: string;
  family_history?: string;
  ecog_score?: number;
}

export interface PatientUpdate extends Partial<PatientCreate> {
  survival_status?: string;
}

// ---------------------------------------------------------------------------
// Somatic Variant
// ---------------------------------------------------------------------------

export interface SomaticVariant {
  id: string;
  patient_id: string;
  gene: string;
  chromosome: string;
  position: number;
  reference: string;
  alternate: string;
  hgvs_c: string | null;
  hgvs_p: string | null;
  variant_allele_frequency: number;
  read_depth: number | null;
  variant_type: string;
  consequence: string | null;
  impact: string | null;
  cosmic_id: string | null;
  oncokb_level: string | null;
  acmg_tier: ACMGTier | null;
  amp_asco_cap_level: AMPASCOCAPLevel | null;
  clinical_significance: string | null;
  citations: string[];
  created_at: string;
}

export interface SomaticVariantCreate {
  patient_id: string;
  gene: string;
  chromosome: string;
  position: number;
  reference: string;
  alternate: string;
  hgvs_c?: string;
  hgvs_p?: string;
  variant_allele_frequency: number;
  read_depth?: number;
  variant_type?: string;
  consequence?: string;
  impact?: string;
}

// ---------------------------------------------------------------------------
// Germline Variant
// ---------------------------------------------------------------------------

export interface GermlineVariant {
  id: string;
  patient_id: string;
  gene: string;
  chromosome: string;
  position: number;
  reference: string;
  alternate: string;
  hgvs_c: string | null;
  hgvs_p: string | null;
  zygosity: string;
  clinvar_id: string | null;
  clinical_significance: string | null;
  acmg_classification: string | null;
  created_at: string;
}

export interface GermlineVariantCreate {
  patient_id: string;
  gene: string;
  chromosome: string;
  position: number;
  reference: string;
  alternate: string;
  hgvs_c?: string;
  hgvs_p?: string;
  zygosity?: string;
  clinvar_id?: string;
  clinical_significance?: string;
}

// ---------------------------------------------------------------------------
// ACMG Classification
// ---------------------------------------------------------------------------

export interface ACMGClassification {
  id: string;
  variant_id: string;
  criteria: ACMGCriteria[];
  classification: string;
  score: number;
  evidence_summary: string;
  classified_by: string;
  classified_at: string;
}

export interface ACMGCriteria {
  code: string;
  category: 'pathogenic' | 'benign';
  strength: 'very_strong' | 'strong' | 'moderate' | 'supporting';
  description: string;
  applied: boolean;
}

// ---------------------------------------------------------------------------
// Treatment Record
// ---------------------------------------------------------------------------

export interface TreatmentRecord {
  id: string;
  patient_id: string;
  treatment_name: string;
  treatment_type: string;
  target_gene: string | null;
  target_variant: string | null;
  start_date: string | null;
  end_date: string | null;
  status: TreatmentStatus;
  response: string | null;
  adverse_events: string | null;
  notes: string | null;
  created_at: string;
}

export interface TreatmentCreate {
  patient_id: string;
  treatment_name: string;
  treatment_type: string;
  target_gene?: string;
  target_variant?: string;
  start_date?: string;
  end_date?: string;
  status?: TreatmentStatus;
  response?: string;
  adverse_events?: string;
  notes?: string;
}

// ---------------------------------------------------------------------------
// Clinical Report
// ---------------------------------------------------------------------------

export interface ClinicalReport {
  id: string;
  patient_id: string;
  report_type: string;
  status: ReportStatus;
  content_md: string | null;
  content_json: string | null;
  generated_at: string | null;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Gene Information
// ---------------------------------------------------------------------------

export interface GeneInfo {
  gene_name: string;
  full_name: string;
  chromosome: string;
  oncogene_type: 'oncogene' | 'tumor_suppressor' | 'both' | 'unknown';
  cosmic_tier: number;
  oncokb_oncogenic: string;
  is_hotspot: boolean;
  hotspot_mutations: HotspotMutation[];
  associated_cancers: string[];
  targeted_drugs: TargetedDrug[];
  description: string;
  citations: string[];
}

export interface HotspotMutation {
  position: string;
  aa_change: string;
  frequency: number;
  oncogenic: string;
}

export interface TargetedDrug {
  drug_name: string;
  target: string;
  biomarker: string;
  approval_status: string;
  efficacy: string;
}

// ---------------------------------------------------------------------------
// Pipeline
// ---------------------------------------------------------------------------

export interface PipelineRunRequest {
  patient_id?: string;
  vcf_file?: File;
  cancer_type?: string;
  options: PipelineOptions;
}

export interface PipelineOptions {
  run_vep: boolean;
  run_phenotype_score: boolean;
  run_ppi_score: boolean;
  run_variant_rank: boolean;
  run_report: boolean;
  top_n_variants: number;
}

export interface PipelineRunStatus {
  run_id: string;
  patient_id: string | null;
  status: 'queued' | 'running' | 'completed' | 'failed';
  phase: string;
  progress: number;
  started_at: string | null;
  completed_at: string | null;
  error: string | null;
}

// ---------------------------------------------------------------------------
// API Response Wrappers
// ---------------------------------------------------------------------------

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface APIError {
  detail: string;
  code?: string;
}

// ---------------------------------------------------------------------------
// System Health
// ---------------------------------------------------------------------------

export interface SystemHealth {
  status: string;
  version: string;
  modules: ModuleHealth[];
}

export interface ModuleHealth {
  name: string;
  port: number;
  healthy: boolean;
  url: string;
}

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------

export interface DashboardStats {
  total_patients: number;
  total_variants: number;
  total_reports: number;
  total_treatments: number;
  recent_patients: CancerPatient[];
  tier_distribution: Record<ACMGTier, number>;
  module_status: ModuleHealthSummary[];
}

export interface ModuleHealthSummary {
  name: string;
  status: 'online' | 'offline' | 'degraded';
  last_checked: string;
}
