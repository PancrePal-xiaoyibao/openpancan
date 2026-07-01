import { useEffect, useState, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { patientsAPI } from '@/services/api';
import { useUIStore, usePatientStore } from '@/store';
import { t } from '@/i18n';
import type { CancerPatient } from '@/types';

// =============================================================================
// Create Patient Modal
// =============================================================================

function CreatePatientModal({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: (patient: CancerPatient) => void;
}) {
  const [form, setForm] = useState({
    patient_code: '',
    diagnosis: 'Pancreatic Ductal Adenocarcinoma',
    gender: 'unknown' as string,
    age: '',
    stage: '',
    tumor_site: 'Pancreas',
    cancer_type: 'Pancreatic Ductal Adenocarcinoma',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.patient_code.trim()) {
      setError('Patient code is required');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      const patient = await patientsAPI.create({
        patient_code: form.patient_code,
        diagnosis: form.diagnosis,
        gender: form.gender as CancerPatient['gender'],
        age: form.age ? parseInt(form.age) : undefined,
        stage: form.stage || undefined,
        tumor_site: form.tumor_site,
        cancer_type: form.cancer_type,
      });
      onCreated(patient);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create patient');
    } finally {
      setSubmitting(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-2xl shadow-elevated w-full max-w-lg p-6 animate-slide-up">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">{t('patient.create')}</h2>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-gray-100">
            <svg className="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">{error}</div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">{t('patient.code')} *</label>
            <input
              className="input"
              value={form.patient_code}
              onChange={(e) => setForm({ ...form, patient_code: e.target.value })}
              placeholder="e.g. PDAC-001"
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">{t('patient.gender')}</label>
              <select
                className="input"
                value={form.gender}
                onChange={(e) => setForm({ ...form, gender: e.target.value })}
              >
                <option value="unknown">Unknown</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label className="label">{t('patient.age')}</label>
              <input
                type="number"
                className="input"
                value={form.age}
                onChange={(e) => setForm({ ...form, age: e.target.value })}
                placeholder="Age"
                min={0}
                max={120}
              />
            </div>
          </div>
          <div>
            <label className="label">{t('patient.diagnosis')}</label>
            <input
              className="input"
              value={form.diagnosis}
              onChange={(e) => setForm({ ...form, diagnosis: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">{t('patient.stage')}</label>
              <select
                className="input"
                value={form.stage}
                onChange={(e) => setForm({ ...form, stage: e.target.value })}
              >
                <option value="">Unknown</option>
                <option value="I">Stage I</option>
                <option value="II">Stage II</option>
                <option value="III">Stage III</option>
                <option value="IV">Stage IV</option>
              </select>
            </div>
            <div>
              <label className="label">{t('patient.tumor_site')}</label>
              <input
                className="input"
                value={form.tumor_site}
                onChange={(e) => setForm({ ...form, tumor_site: e.target.value })}
              />
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">
              {t('common.cancel')}
            </button>
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? t('common.loading') : t('common.create')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// =============================================================================
// Patient List Page
// =============================================================================

export default function PatientList() {
  const navigate = useNavigate();
  const { language } = useUIStore();
  const { patients, setPatients, loading, setLoading, error, setError } = usePatientStore();
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showCreate, setShowCreate] = useState(false);

  const loadPatients = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await patientsAPI.list({
        search: search || undefined,
        page,
        page_size: 20,
      });
      setPatients(response.items);
      setTotalPages(response.total_pages);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load patients');
      setPatients([]);
    } finally {
      setLoading(false);
    }
  }, [search, page, setPatients, setLoading, setError]);

  useEffect(() => {
    loadPatients();
  }, [loadPatients]);

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this patient? This action cannot be undone.')) return;
    try {
      await patientsAPI.delete(id);
      setPatients(patients.filter((p) => p.id !== id));
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete');
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('patient.title')}</h1>
          <p className="text-sm text-gray-500 mt-1">
            {patients.length > 0 ? `${patients.length} patients` : ''}
          </p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          {t('patient.create')}
        </button>
      </div>

      {/* Search bar */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            className="input pl-10"
            placeholder={t('patient.search_placeholder')}
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          />
        </div>
        <button onClick={loadPatients} className="btn-secondary" title={t('common.refresh')}>
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>
      )}

      {/* Table */}
      {loading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="skeleton h-14 rounded-lg" />
          ))}
        </div>
      ) : patients.length === 0 ? (
        <div className="card p-12 text-center">
          <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <p className="text-gray-500 text-sm">{t('patient.no_patients')}</p>
          <button onClick={() => setShowCreate(true)} className="btn-primary mt-4">
            {t('patient.create')}
          </button>
        </div>
      ) : (
        <>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>{t('patient.code')}</th>
                  <th>{t('patient.diagnosis')}</th>
                  <th>{t('patient.age')}</th>
                  <th>{t('patient.gender')}</th>
                  <th>{t('patient.stage')}</th>
                  <th>{t('patient.created')}</th>
                  <th className="w-20">{t('common.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {patients.map((patient) => (
                  <tr key={patient.id}>
                    <td>
                      <button
                        onClick={() => navigate(`/patients/${patient.id}`)}
                        className="text-primary-600 hover:underline font-medium text-left"
                      >
                        {patient.patient_code}
                      </button>
                    </td>
                    <td className="text-gray-600 max-w-xs truncate">{patient.diagnosis}</td>
                    <td className="text-gray-500">{patient.age ?? '-'}</td>
                    <td className="text-gray-500 capitalize">{patient.gender}</td>
                    <td>
                      {patient.stage ? (
                        <span className="badge-blue">{patient.stage}</span>
                      ) : '-'}
                    </td>
                    <td className="text-gray-500 text-xs">
                      {patient.created_at ? new Date(patient.created_at).toLocaleDateString() : '-'}
                    </td>
                    <td>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => navigate(`/patients/${patient.id}`)}
                          className="p-1 rounded hover:bg-gray-100 text-gray-500"
                          title={t('common.details')}
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => handleDelete(patient.id)}
                          className="p-1 rounded hover:bg-red-50 text-gray-400 hover:text-red-500"
                          title={t('common.delete')}
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-500">
                Page {page} of {totalPages}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="btn-secondary btn-sm"
                >
                  {t('common.previous')}
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="btn-secondary btn-sm"
                >
                  {t('common.next')}
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Create Modal */}
      <CreatePatientModal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        onCreated={(patient) => {
          setPatients([patient, ...patients]);
          navigate(`/patients/${patient.id}`);
        }}
      />
    </div>
  );
}
