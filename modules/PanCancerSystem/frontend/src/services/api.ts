// =============================================================================
// OpenPanCan - API Client
// =============================================================================
//
// Axios-based API client for the PanCancerSystem backend.
// All requests go through the Vite proxy (/api -> backend:8007) in development,
// or through nginx proxy in production.
//
// =============================================================================

import axios, { AxiosInstance, AxiosResponse } from 'axios';
import type {
  CancerPatient,
  PatientCreate,
  PatientUpdate,
  SomaticVariant,
  SomaticVariantCreate,
  GermlineVariant,
  GermlineVariantCreate,
  ACMGClassification,
  TreatmentRecord,
  TreatmentCreate,
  ClinicalReport,
  GeneInfo,
  PipelineRunRequest,
  PipelineRunStatus,
  SystemHealth,
  DashboardStats,
  PaginatedResponse,
} from '@/types';

// ---------------------------------------------------------------------------
// Axios instance
// ---------------------------------------------------------------------------

const BASE_URL = '/api';

const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ---------------------------------------------------------------------------
// Response interceptor – unwrap data, handle errors
// ---------------------------------------------------------------------------

api.interceptors.response.use(
  (response: AxiosResponse) => response.data,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred';
    console.error('[API Error]', message, error.response?.status);
    return Promise.reject(new Error(message));
  },
);

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

export const healthAPI = {
  check: (): Promise<SystemHealth> => api.get('/health'),
};

// ---------------------------------------------------------------------------
// Patients
// ---------------------------------------------------------------------------

export const patientsAPI = {
  /** List all patients with optional search and pagination */
  list: (params?: {
    search?: string;
    page?: number;
    page_size?: number;
    cancer_type?: string;
    stage?: string;
  }): Promise<PaginatedResponse<CancerPatient>> =>
    api.get('/patients', { params }),

  /** Get a single patient by ID */
  get: (id: string): Promise<CancerPatient> =>
    api.get(`/patients/${id}`),

  /** Create a new patient */
  create: (data: PatientCreate): Promise<CancerPatient> =>
    api.post('/patients', data),

  /** Update an existing patient */
  update: (id: string, data: PatientUpdate): Promise<CancerPatient> =>
    api.put(`/patients/${id}`, data),

  /** Delete a patient */
  delete: (id: string): Promise<void> =>
    api.delete(`/patients/${id}`),
};

// ---------------------------------------------------------------------------
// Somatic Variants
// ---------------------------------------------------------------------------

export const somaticVariantsAPI = {
  /** List somatic variants for a patient */
  list: (patientId: string, params?: {
    gene?: string;
    acmg_tier?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<SomaticVariant>> =>
    api.get(`/patients/${patientId}/variants/somatic`, { params }),

  /** Get a single somatic variant */
  get: (variantId: string): Promise<SomaticVariant> =>
    api.get(`/variants/somatic/${variantId}`),

  /** Create a somatic variant */
  create: (data: SomaticVariantCreate): Promise<SomaticVariant> =>
    api.post('/variants/somatic', data),

  /** Update a somatic variant */
  update: (variantId: string, data: Partial<SomaticVariantCreate>): Promise<SomaticVariant> =>
    api.put(`/variants/somatic/${variantId}`, data),

  /** Delete a somatic variant */
  delete: (variantId: string): Promise<void> =>
    api.delete(`/variants/somatic/${variantId}`),

  /** Get ACMG classification for a somatic variant */
  getACMG: (variantId: string): Promise<ACMGClassification> =>
    api.get(`/variants/somatic/${variantId}/acmg`),

  /** Run ACMG classification */
  classifyACMG: (variantId: string): Promise<ACMGClassification> =>
    api.post(`/variants/somatic/${variantId}/acmg/classify`),
};

// ---------------------------------------------------------------------------
// Germline Variants
// ---------------------------------------------------------------------------

export const germlineVariantsAPI = {
  /** List germline variants for a patient */
  list: (patientId: string, params?: {
    gene?: string;
    clinical_significance?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<GermlineVariant>> =>
    api.get(`/patients/${patientId}/variants/germline`, { params }),

  /** Get a single germline variant */
  get: (variantId: string): Promise<GermlineVariant> =>
    api.get(`/variants/germline/${variantId}`),

  /** Create a germline variant */
  create: (data: GermlineVariantCreate): Promise<GermlineVariant> =>
    api.post('/variants/germline', data),

  /** Update a germline variant */
  update: (variantId: string, data: Partial<GermlineVariantCreate>): Promise<GermlineVariant> =>
    api.put(`/variants/germline/${variantId}`, data),

  /** Delete a germline variant */
  delete: (variantId: string): Promise<void> =>
    api.delete(`/variants/germline/${variantId}`),
};

// ---------------------------------------------------------------------------
// Variant Browser (combined somatic + germline)
// ---------------------------------------------------------------------------

export const variantBrowserAPI = {
  /** Search variants across all patients */
  search: (params: {
    gene?: string;
    type?: 'somatic' | 'germline';
    acmg_tier?: string;
    vaf_min?: number;
    vaf_max?: number;
    clinical_significance?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<SomaticVariant | GermlineVariant>> =>
    api.get('/variants/search', { params }),
};

// ---------------------------------------------------------------------------
// ACMG Classification
// ---------------------------------------------------------------------------

export const acmgAPI = {
  /** Get ACMG classification for a variant */
  get: (variantId: string): Promise<ACMGClassification> =>
    api.get(`/acmg/${variantId}`),

  /** Run ACMG classification for a variant */
  classify: (variantId: string): Promise<ACMGClassification> =>
    api.post(`/acmg/${variantId}/classify`),

  /** Batch classify variants */
  batchClassify: (variantIds: string[]): Promise<ACMGClassification[]> =>
    api.post('/acmg/batch-classify', { variant_ids: variantIds }),
};

// ---------------------------------------------------------------------------
// Reports
// ---------------------------------------------------------------------------

export const reportsAPI = {
  /** List reports for a patient */
  list: (patientId: string): Promise<ClinicalReport[]> =>
    api.get(`/patients/${patientId}/reports`),

  /** Get a specific report */
  get: (reportId: string): Promise<ClinicalReport> =>
    api.get(`/reports/${reportId}`),

  /** Generate a report for a patient */
  generate: (patientId: string, options?: {
    include_treatments?: boolean;
    include_trials?: boolean;
    top_n_variants?: number;
  }): Promise<{ run_id: string; status: string }> =>
    api.post(`/patients/${patientId}/reports/generate`, options),

  /** Download report markdown */
  download: (reportId: string, format: 'md' | 'json' | 'pdf'): Promise<Blob> =>
    api.get(`/reports/${reportId}/download`, {
      params: { format },
      responseType: 'blob',
    }),

  /** Delete a report */
  delete: (reportId: string): Promise<void> =>
    api.delete(`/reports/${reportId}`),
};

// ---------------------------------------------------------------------------
// Treatment Records
// ---------------------------------------------------------------------------

export const treatmentsAPI = {
  /** List treatments for a patient */
  list: (patientId: string): Promise<TreatmentRecord[]> =>
    api.get(`/patients/${patientId}/treatments`),

  /** Get a specific treatment */
  get: (treatmentId: string): Promise<TreatmentRecord> =>
    api.get(`/treatments/${treatmentId}`),

  /** Create a treatment record */
  create: (data: TreatmentCreate): Promise<TreatmentRecord> =>
    api.post('/treatments', data),

  /** Update a treatment record */
  update: (treatmentId: string, data: Partial<TreatmentCreate>): Promise<TreatmentRecord> =>
    api.put(`/treatments/${treatmentId}`, data),

  /** Delete a treatment record */
  delete: (treatmentId: string): Promise<void> =>
    api.delete(`/treatments/${treatmentId}`),
};

// ---------------------------------------------------------------------------
// Gene Information
// ---------------------------------------------------------------------------

export const genesAPI = {
  /** Get gene information */
  get: (geneName: string): Promise<GeneInfo> =>
    api.get(`/genes/${geneName}`),

  /** Search genes */
  search: (query: string): Promise<GeneInfo[]> =>
    api.get('/genes/search', { params: { q: query } }),

  /** List known pancreatic cancer driver genes */
  listDrivers: (): Promise<GeneInfo[]> =>
    api.get('/genes/drivers'),
};

// ---------------------------------------------------------------------------
// Pipeline
// ---------------------------------------------------------------------------

export const pipelineAPI = {
  /** Start a pipeline run */
  start: (data: PipelineRunRequest): Promise<{ run_id: string }> =>
    api.post('/pipeline/run', data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  /** Get pipeline run status */
  status: (runId: string): Promise<PipelineRunStatus> =>
    api.get(`/pipeline/runs/${runId}`),

  /** List pipeline runs */
  list: (params?: {
    page?: number;
    page_size?: number;
    status?: string;
  }): Promise<PaginatedResponse<PipelineRunStatus>> =>
    api.get('/pipeline/runs', { params }),
};

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------

export const dashboardAPI = {
  /** Get dashboard statistics */
  stats: (): Promise<DashboardStats> =>
    api.get('/dashboard/stats'),
};

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

export const settingsAPI = {
  /** Get system settings */
  get: (): Promise<Record<string, unknown>> =>
    api.get('/settings'),

  /** Update system settings */
  update: (settings: Record<string, unknown>): Promise<Record<string, unknown>> =>
    api.put('/settings', settings),
};

// ---------------------------------------------------------------------------
// Default export for convenience
// ---------------------------------------------------------------------------

export default api;
