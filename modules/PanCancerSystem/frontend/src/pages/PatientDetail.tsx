import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { patientsAPI, somaticVariantsAPI, germlineVariantsAPI, treatmentsAPI, reportsAPI } from '@/services/api';
import { useUIStore, usePatientStore } from '@/store';
import { t } from '@/i18n';
import BiomarkerPanel from '@/components/BiomarkerPanel';
import TumorProfile from '@/components/TumorProfile';
import type { CancerPatient, SomaticVariant, GermlineVariant, TreatmentRecord, ClinicalReport } from '@/types';

// =============================================================================
// Tab definitions
// =============================================================================

type Tab = 'overview' | 'variants' | 'treatments' | 'reports';

const tabs: { key: Tab; label: string }[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'variants', label: 'Variants' },
  { key: 'treatments', label: 'Treatments' },
  { key: 'reports', label: 'Reports' },
];

// =============================================================================
// Info Row
// =============================================================================

function InfoRow({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="flex justify-between py-2 border-b border-gray-50 last:border-0">
      <span className="text-sm text-gray-500">{label}</span>
      <span className="text-sm font-medium text-gray-900">{value ?? '-'}</span>
    </div>
  );
}

// =============================================================================
// Patient Detail Page
// =============================================================================

export default function PatientDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { language } = useUIStore();
  const { selectPatient } = usePatientStore();

  const [patient, setPatient] = useState<CancerPatient | null>(null);
  const [somaticVariants, setSomaticVariants] = useState<SomaticVariant[]>([]);
  const [germlineVariants, setGermlineVariants] = useState<GermlineVariant[]>([]);
  const [treatments, setTreatments] = useState<TreatmentRecord[]>([]);
  const [reports, setReports] = useState<ClinicalReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<Tab>('overview');

  useEffect(() => {
    if (!id) return;
    async function load() {
      setLoading(true);
      try {
        const [p, sv, gv, t, r] = await Promise.all([
          patientsAPI.get(id),
          somaticVariantsAPI.list(id).catch(() => ({ items: [], total: 0, page: 1, page_size: 20, total_pages: 0 })),
          germlineVariantsAPI.list(id).catch(() => ({ items: [], total: 0, page: 1, page_size: 20, total_pages: 0 })),
          treatmentsAPI.list(id).catch(() => []),
          reportsAPI.list(id).catch(() => []),
        ]);
        setPatient(p);
        selectPatient(p);
        setSomaticVariants(sv.items);
        setGermlineVariants(gv.items);
        setTreatments(t);
        setReports(r);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load patient');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id, selectPatient]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="skeleton h-8 w-48" />
        <div className="skeleton h-64 rounded-xl" />
      </div>
    );
  }

  if (error || !patient) {
    return (
      <div className="card p-8 text-center">
        <p className="text-red-600 mb-4">{error || 'Patient not found'}</p>
        <Link to="/patients" className="btn-secondary">{t('common.back')}</Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link to="/patients" className="hover:text-primary-600">{t('patient.title')}</Link>
        <span>/</span>
        <span className="text-gray-900 font-medium">{patient.patient_code}</span>
      </div>

      {/* Patient header */}
      <div className="card p-6">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-xl font-bold text-gray-900">{patient.patient_code}</h1>
            <p className="text-gray-500 mt-1">{patient.diagnosis}</p>
            <div className="flex items-center gap-2 mt-2">
              {patient.stage && <span className="badge-blue">{patient.stage}</span>}
              {patient.cancer_type && <span className="badge-purple">{patient.cancer_type}</span>}
              <span className={`badge ${patient.survival_status === 'alive' ? 'badge-green' : 'badge-gray'}`}>
                {patient.survival_status}
              </span>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => navigate(`/variants/${patient.id}`)}
              className="btn-primary btn-sm"
            >
              View All Variants
            </button>
            <button
              onClick={() => navigate(`/reports/${patient.id}`)}
              className="btn-secondary btn-sm"
            >
              View Reports
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors
              ${activeTab === tab.key
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Demographics */}
          <div className="card">
            <div className="card-header">
              <h3 className="font-semibold text-gray-900">{t('patient.demographics')}</h3>
            </div>
            <div className="card-body">
              <InfoRow label={t('patient.code')} value={patient.patient_code} />
              <InfoRow label={t('patient.age')} value={patient.age} />
              <InfoRow label={t('patient.gender')} value={patient.gender} />
              <InfoRow label={t('patient.survival')} value={patient.survival_status} />
              <InfoRow label={t('patient.created')} value={patient.created_at ? new Date(patient.created_at).toLocaleDateString() : null} />
            </div>
          </div>

          {/* Clinical Info */}
          <div className="card">
            <div className="card-header">
              <h3 className="font-semibold text-gray-900">{t('patient.clinical_info')}</h3>
            </div>
            <div className="card-body">
              <InfoRow label={t('patient.diagnosis')} value={patient.diagnosis} />
              <InfoRow label={t('patient.cancer_type')} value={patient.cancer_type} />
              <InfoRow label={t('patient.stage')} value={patient.stage} />
              <InfoRow label={t('patient.tumor_site')} value={patient.tumor_site} />
              <InfoRow label="Histological Type" value={patient.histological_type} />
              <InfoRow label="Grade" value={patient.grade} />
              <InfoRow label="ECOG Score" value={patient.ecog_score} />
            </div>
          </div>

          {/* Biomarker Panel */}
          <div className="lg:col-span-2">
            <BiomarkerPanel variants={somaticVariants} germlineVariants={germlineVariants} />
          </div>

          {/* Tumor Profile */}
          {somaticVariants.length > 0 && (
            <div className="lg:col-span-2">
              <TumorProfile variants={somaticVariants} />
            </div>
          )}
        </div>
      )}

      {activeTab === 'variants' && (
        <div className="space-y-4">
          {/* Somatic variants */}
          <div className="card">
            <div className="card-header">
              <h3 className="font-semibold text-gray-900">Somatic Variants ({somaticVariants.length})</h3>
            </div>
            {somaticVariants.length === 0 ? (
              <div className="card-body">
                <p className="text-sm text-gray-400">{t('variant.no_variants')}</p>
              </div>
            ) : (
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>{t('variant.gene')}</th>
                      <th>{t('variant.hgvs_p')}</th>
                      <th>{t('variant.vaf')}</th>
                      <th>{t('variant.cosmic')}</th>
                      <th>{t('variant.acmg_tier')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {somaticVariants.map((v) => (
                      <tr key={v.id}>
                        <td>
                          <Link to={`/variants/${patient.id}`} className="text-primary-600 hover:underline font-medium">
                            {v.gene}
                          </Link>
                        </td>
                        <td className="font-mono text-xs text-gray-600">{v.hgvs_p || '-'}</td>
                        <td>
                          <span className={v.variant_allele_frequency > 0.3 ? 'text-amber-600 font-medium' : 'text-gray-600'}>
                            {(v.variant_allele_frequency * 100).toFixed(1)}%
                          </span>
                        </td>
                        <td className="text-xs">{v.cosmic_id || '-'}</td>
                        <td>
                          {v.acmg_tier ? (
                            <span className={`badge text-xs ${getTierBadge(v.acmg_tier)}`}>{v.acmg_tier}</span>
                          ) : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Germline variants */}
          {germlineVariants.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h3 className="font-semibold text-gray-900">Germline Variants ({germlineVariants.length})</h3>
              </div>
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>{t('variant.gene')}</th>
                      <th>{t('variant.hgvs_p')}</th>
                      <th>Zygosity</th>
                      <th>ClinVar</th>
                      <th>{t('variant.clinical_sig')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {germlineVariants.map((v) => (
                      <tr key={v.id}>
                        <td className="font-medium text-primary-600">{v.gene}</td>
                        <td className="font-mono text-xs text-gray-600">{v.hgvs_p || '-'}</td>
                        <td>{v.zygosity}</td>
                        <td className="text-xs">{v.clinvar_id || '-'}</td>
                        <td>
                          {v.clinical_significance ? (
                            <span className="badge-gray text-xs">{v.clinical_significance}</span>
                          ) : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'treatments' && (
        <div className="card">
          <div className="card-header">
            <h3 className="font-semibold text-gray-900">{t('treatment.title')} ({treatments.length})</h3>
            <button className="btn-primary btn-sm">{t('treatment.add')}</button>
          </div>
          {treatments.length === 0 ? (
            <div className="card-body">
              <p className="text-sm text-gray-400">{t('treatment.no_treatments')}</p>
            </div>
          ) : (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>{t('treatment.name')}</th>
                    <th>{t('treatment.type')}</th>
                    <th>{t('treatment.target')}</th>
                    <th>{t('treatment.start')}</th>
                    <th>{t('treatment.response')}</th>
                    <th>{t('treatment.status')}</th>
                  </tr>
                </thead>
                <tbody>
                  {treatments.map((t) => (
                    <tr key={t.id}>
                      <td className="font-medium">{t.treatment_name}</td>
                      <td className="text-gray-500">{t.treatment_type}</td>
                      <td className="text-gray-500">{t.target_gene || '-'}</td>
                      <td className="text-xs text-gray-500">
                        {t.start_date ? new Date(t.start_date).toLocaleDateString() : '-'}
                      </td>
                      <td>
                        {t.response ? (
                          <span className="badge-blue text-xs">{t.response}</span>
                        ) : '-'}
                      </td>
                      <td>
                        <span className={`badge text-xs ${getTreatmentStatusBadge(t.status)}`}>
                          {t.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === 'reports' && (
        <div className="card">
          <div className="card-header">
            <h3 className="font-semibold text-gray-900">{t('report.title')} ({reports.length})</h3>
            <button
              className="btn-primary btn-sm"
              onClick={() => navigate(`/reports/${patient.id}`)}
            >
              {t('report.generate')}
            </button>
          </div>
          {reports.length === 0 ? (
            <div className="card-body">
              <p className="text-sm text-gray-400">{t('report.no_reports')}</p>
            </div>
          ) : (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>{t('report.type')}</th>
                    <th>{t('report.status')}</th>
                    <th>{t('report.generated_at')}</th>
                    <th>{t('common.actions')}</th>
                  </tr>
                </thead>
                <tbody>
                  {reports.map((r) => (
                    <tr key={r.id}>
                      <td className="font-medium">{r.report_type}</td>
                      <td>
                        <span className={`badge text-xs ${getReportStatusBadge(r.status)}`}>{r.status}</span>
                      </td>
                      <td className="text-xs text-gray-500">
                        {r.generated_at ? new Date(r.generated_at).toLocaleDateString() : '-'}
                      </td>
                      <td>
                        <button
                          onClick={() => navigate(`/reports/${r.id}`)}
                          className="btn-ghost btn-sm"
                        >
                          {t('common.details')}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Helpers
// =============================================================================

function getTierBadge(tier: string): string {
  switch (tier) {
    case 'I': return 'badge-green';
    case 'II': return 'badge-blue';
    case 'III': return 'badge-amber';
    case 'IV': return 'badge-red';
    default: return 'badge-gray';
  }
}

function getTreatmentStatusBadge(status: string): string {
  switch (status) {
    case 'ongoing': return 'badge-blue';
    case 'completed': return 'badge-green';
    case 'planned': return 'badge-purple';
    case 'discontinued': return 'badge-red';
    default: return 'badge-gray';
  }
}

function getReportStatusBadge(status: string): string {
  switch (status) {
    case 'completed': return 'badge-green';
    case 'generating': return 'badge-amber';
    case 'draft': return 'badge-gray';
    case 'failed': return 'badge-red';
    default: return 'badge-gray';
  }
}
