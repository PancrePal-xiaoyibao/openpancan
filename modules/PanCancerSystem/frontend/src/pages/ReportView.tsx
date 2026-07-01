import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { reportsAPI } from '@/services/api';
import { useUIStore } from '@/store';
import { t } from '@/i18n';
import type { ClinicalReport } from '@/types';

// =============================================================================
// Report View Page
// =============================================================================

export default function ReportView() {
  const { patientId } = useParams<{ patientId?: string }>();
  const { language } = useUIStore();

  const [reports, setReports] = useState<ClinicalReport[]>([]);
  const [selectedReport, setSelectedReport] = useState<ClinicalReport | null>(null);
  const [reportContent, setReportContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState('');

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        if (patientId) {
          const reportList = await reportsAPI.list(patientId);
          setReports(reportList);
          if (reportList.length > 0) {
            setSelectedReport(reportList[0]);
            setReportContent(reportList[0].content_md || '');
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load reports');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [patientId]);

  const handleGenerate = async () => {
    if (!patientId) return;
    setGenerating(true);
    setGenerateError('');
    try {
      const result = await reportsAPI.generate(patientId);
      // Poll for completion or just reload
      setTimeout(async () => {
        try {
          const updatedReports = await reportsAPI.list(patientId);
          setReports(updatedReports);
        } catch {
          // ignore
        }
        setGenerating(false);
      }, 3000);
    } catch (err) {
      setGenerateError(err instanceof Error ? err.message : 'Failed to generate report');
      setGenerating(false);
    }
  };

  const handleDownload = async (reportId: string, format: 'md' | 'json') => {
    try {
      const blob = await reportsAPI.download(reportId, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `openpancan_report_${reportId}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Download failed');
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="skeleton h-8 w-48" />
        <div className="skeleton h-96 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('report.title')}</h1>
          {patientId && (
            <p className="text-sm text-gray-500 mt-1">
              <Link to={`/patients/${patientId}`} className="text-primary-600 hover:underline">
                Patient {patientId}
              </Link>
            </p>
          )}
        </div>
        {patientId && (
          <button
            onClick={handleGenerate}
            className="btn-primary"
            disabled={generating}
          >
            {generating ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {t('report.generating')}
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                {t('report.generate')}
              </>
            )}
          </button>
        )}
      </div>

      {generateError && (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg text-sm">{generateError}</div>
      )}
      {error && (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>
      )}

      {reports.length === 0 && !patientId ? (
        <div className="card p-12 text-center">
          <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="text-gray-500 text-sm">{t('report.no_reports')}</p>
          <p className="text-gray-400 text-xs mt-1">Select a patient to generate a report</p>
        </div>
      ) : reports.length === 0 ? (
        <div className="card p-12 text-center">
          <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-gray-500 text-sm">{t('report.no_reports')}</p>
          <p className="text-gray-400 text-xs mt-1">Click "Generate Report" to create one</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Report list sidebar */}
          <div className="card lg:col-span-1">
            <div className="card-header">
              <h3 className="font-semibold text-gray-900">Reports ({reports.length})</h3>
            </div>
            <div className="divide-y divide-gray-100">
              {reports.map((r) => (
                <button
                  key={r.id}
                  onClick={() => {
                    setSelectedReport(r);
                    setReportContent(r.content_md || '');
                  }}
                  className={`w-full text-left p-4 hover:bg-gray-50 transition-colors
                    ${selectedReport?.id === r.id ? 'bg-blue-50 border-l-4 border-primary-500' : ''}`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-900">{r.report_type}</span>
                    <span className={`badge text-2xs ${getReportStatusBadge(r.status)}`}>
                      {r.status}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mt-1">
                    {r.generated_at ? new Date(r.generated_at).toLocaleString() : r.created_at ? new Date(r.created_at).toLocaleString() : '-'}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* Report content */}
          <div className="card lg:col-span-2">
            <div className="card-header">
              <h3 className="font-semibold text-gray-900">
                {selectedReport?.report_type || 'Report'} Preview
              </h3>
              <div className="flex gap-2">
                {selectedReport && (
                  <>
                    <button
                      onClick={() => handleDownload(selectedReport.id, 'md')}
                      className="btn-secondary btn-sm"
                    >
                      {t('report.download_md')}
                    </button>
                    <button
                      onClick={() => handleDownload(selectedReport.id, 'json')}
                      className="btn-ghost btn-sm"
                    >
                      {t('report.download_json')}
                    </button>
                  </>
                )}
              </div>
            </div>
            <div className="card-body min-h-[500px]">
              {reportContent ? (
                <div className="prose prose-sm max-w-none">
                  <pre className="whitespace-pre-wrap font-mono text-sm text-gray-700 bg-gray-50 p-4 rounded-lg overflow-auto max-h-[600px]">
                    {reportContent}
                  </pre>
                </div>
              ) : (
                <div className="flex items-center justify-center h-64 text-gray-400 text-sm">
                  {selectedReport ? 'Report content not available' : 'Select a report to view'}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
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
