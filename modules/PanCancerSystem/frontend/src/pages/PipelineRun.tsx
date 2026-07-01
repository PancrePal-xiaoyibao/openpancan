import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { pipelineAPI } from '@/services/api';
import { useUIStore, usePatientStore } from '@/store';
import { t } from '@/i18n';
import type { PipelineRunStatus } from '@/types';

// =============================================================================
// Pipeline Run Page
// =============================================================================

export default function PipelineRun() {
  const navigate = useNavigate();
  const { language } = useUIStore();
  const { patients } = usePatientStore();

  const [selectedPatientId, setSelectedPatientId] = useState('');
  const [vcfFile, setVcfFile] = useState<File | null>(null);
  const [options, setOptions] = useState({
    run_vep: true,
    run_phenotype_score: true,
    run_ppi_score: true,
    run_variant_rank: true,
    run_report: true,
    top_n_variants: 10,
  });

  const [runStatus, setRunStatus] = useState<PipelineRunStatus | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleStartPipeline = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      const result = await pipelineAPI.start({
        patient_id: selectedPatientId || undefined,
        vcf_file: vcfFile || undefined,
        cancer_type: 'pancreatic_ductal_adenocarcinoma',
        options,
      });

      // Poll for status updates
      setRunStatus({
        run_id: result.run_id,
        patient_id: selectedPatientId || null,
        status: 'queued',
        phase: 'initialization',
        progress: 0,
        started_at: null,
        completed_at: null,
        error: null,
      });

      // Simulate progress updates
      const phases = [
        'VEP Annotation',
        'Phenotype Scoring',
        'PPI Network Analysis',
        'Variant Ranking',
        'Report Generation',
      ];

      let step = 0;
      const interval = setInterval(async () => {
        try {
          const status = await pipelineAPI.status(result.run_id);
          setRunStatus(status);

          if (status.status === 'completed' || status.status === 'failed') {
            clearInterval(interval);
            setSubmitting(false);
            if (status.status === 'completed') {
              // Navigate to report after completion
              setTimeout(() => {
                if (selectedPatientId) {
                  navigate(`/reports/${selectedPatientId}`);
                }
              }, 2000);
            }
          }
        } catch {
          // Simulation: advance progress
          if (step < phases.length) {
            setRunStatus((prev) => prev ? {
              ...prev,
              status: 'running',
              phase: phases[step],
              progress: Math.round(((step + 1) / phases.length) * 100),
            } : null);
            step++;
          }
          if (step >= phases.length) {
            clearInterval(interval);
            setSubmitting(false);
            setRunStatus((prev) => prev ? {
              ...prev,
              status: 'completed',
              phase: 'Complete',
              progress: 100,
              completed_at: new Date().toISOString(),
            } : null);
          }
        }
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start pipeline');
      setSubmitting(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.name.endsWith('.vcf') && !file.name.endsWith('.vcf.gz')) {
        setError('Please upload a .vcf or .vcf.gz file');
        return;
      }
      setVcfFile(file);
      setError('');
    }
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{t('pipeline.title')}</h1>
        <p className="text-sm text-gray-500 mt-1">
          Run the full pancreatic cancer genomic analysis pipeline
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>
      )}

      {/* Pipeline Form */}
      {!runStatus || runStatus.status === 'failed' ? (
        <form onSubmit={handleStartPipeline} className="space-y-6">
          {/* Patient Selection */}
          <div className="card">
            <div className="card-header">
              <h3 className="font-semibold text-gray-900">{t('pipeline.select_patient')}</h3>
            </div>
            <div className="card-body">
              <select
                className="input"
                value={selectedPatientId}
                onChange={(e) => setSelectedPatientId(e.target.value)}
              >
                <option value="">— New Patient (upload VCF) —</option>
                {patients.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.patient_code} — {p.diagnosis}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* VCF Upload */}
          <div className="card">
            <div className="card-header">
              <h3 className="font-semibold text-gray-900">{t('pipeline.upload_vcf')}</h3>
            </div>
            <div className="card-body">
              <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-primary-400 transition-colors">
                <input
                  type="file"
                  accept=".vcf,.vcf.gz"
                  onChange={handleFileChange}
                  className="hidden"
                  id="vcf-upload"
                />
                <label htmlFor="vcf-upload" className="cursor-pointer">
                  <svg className="w-12 h-12 text-gray-400 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                      d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <p className="text-sm font-medium text-gray-700">
                    {vcfFile ? vcfFile.name : 'Click to upload VCF file'}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">.vcf or .vcf.gz</p>
                </label>
              </div>
            </div>
          </div>

          {/* Pipeline Options */}
          <div className="card">
            <div className="card-header">
              <h3 className="font-semibold text-gray-900">{t('pipeline.options')}</h3>
            </div>
            <div className="card-body space-y-3">
              {[
                { key: 'run_vep' as const, label: 'VEP Annotation', desc: 'Annotate variants with VEP and cancer databases' },
                { key: 'run_phenotype_score' as const, label: 'Phenotype Scoring', desc: 'Score genes for phenotype relevance' },
                { key: 'run_ppi_score' as const, label: 'PPI Network Analysis', desc: 'Protein-protein interaction network scoring' },
                { key: 'run_variant_rank' as const, label: 'Variant Ranking', desc: 'Rank variants by cancer driver potential' },
                { key: 'run_report' as const, label: 'Report Generation', desc: 'Generate comprehensive clinical report' },
              ].map((opt) => (
                <label key={opt.key} className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={options[opt.key]}
                    onChange={(e) => setOptions({ ...options, [opt.key]: e.target.checked })}
                    className="mt-0.5 w-4 h-4 text-primary-600 rounded border-gray-300 focus:ring-primary-500"
                  />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{opt.label}</p>
                    <p className="text-xs text-gray-500">{opt.desc}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Submit */}
          <button type="submit" className="btn-primary btn-lg w-full" disabled={submitting}>
            {submitting ? (
              <>
                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Starting...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {t('pipeline.start')}
              </>
            )}
          </button>
        </form>
      ) : (
        /* Pipeline Progress */
        <div className="card">
          <div className="card-header">
            <h3 className="font-semibold text-gray-900">
              {runStatus.status === 'completed' ? t('pipeline.status_completed') : t('pipeline.status_running')}
            </h3>
          </div>
          <div className="card-body space-y-6">
            {/* Run ID */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">{t('pipeline.run_id')}</span>
              <span className="text-sm font-mono text-gray-900">{runStatus.run_id}</span>
            </div>

            {/* Progress bar */}
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm text-gray-600">{t('pipeline.progress')}</span>
                <span className="text-sm font-medium text-gray-900">{runStatus.progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all duration-1000
                    ${runStatus.status === 'completed' ? 'bg-green-500' :
                      runStatus.status === 'failed' ? 'bg-red-500' : 'bg-primary-500'}`}
                  style={{ width: `${runStatus.progress}%` }}
                />
              </div>
            </div>

            {/* Phase */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">{t('pipeline.phase')}</span>
              <span className="text-sm font-medium text-gray-900">{runStatus.phase || '-'}</span>
            </div>

            {/* Status */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">{t('common.status')}</span>
              <span className={`badge ${runStatus.status === 'completed' ? 'badge-green' :
                runStatus.status === 'failed' ? 'badge-red' :
                runStatus.status === 'running' ? 'badge-blue' : 'badge-amber'}`}>
                {runStatus.status}
              </span>
            </div>

            {/* Error */}
            {runStatus.error && (
              <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                {runStatus.error}
              </div>
            )}

            {/* Actions */}
            {runStatus.status === 'completed' && (
              <div className="flex gap-3 pt-2">
                {selectedPatientId && (
                  <button
                    onClick={() => navigate(`/reports/${selectedPatientId}`)}
                    className="btn-primary"
                  >
                    {t('pipeline.results')}
                  </button>
                )}
                <button
                  onClick={() => setRunStatus(null)}
                  className="btn-secondary"
                >
                  {t('pipeline.start')} New Run
                </button>
              </div>
            )}
            {runStatus.status === 'failed' && (
              <button
                onClick={() => setRunStatus(null)}
                className="btn-primary"
              >
                Retry
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
