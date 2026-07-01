import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { dashboardAPI, healthAPI } from '@/services/api';
import { useUIStore } from '@/store';
import { t } from '@/i18n';
import type { DashboardStats, SystemHealth } from '@/types';

// =============================================================================
// Stat Card
// =============================================================================

function StatCard({
  label,
  value,
  icon,
  color,
  to,
}: {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  color: string;
  to?: string;
}) {
  const content = (
    <div className="card p-6 flex items-center gap-4 hover:shadow-elevated transition-shadow cursor-pointer">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${color}`}>
        {icon}
      </div>
      <div>
        <p className="text-3xl font-bold text-gray-900">{value}</p>
        <p className="text-sm text-gray-500">{label}</p>
      </div>
    </div>
  );

  return to ? <Link to={to}>{content}</Link> : content;
}

// =============================================================================
// Module Status Row
// =============================================================================

function ModuleStatusRow({ name, healthy }: { name: string; healthy: boolean }) {
  return (
    <div className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-gray-50 transition-colors">
      <span className="text-sm text-gray-700">{name}</span>
      <span className={`flex items-center gap-1.5 text-xs font-medium
        ${healthy ? 'text-green-700' : 'text-red-700'}`}>
        <span className={healthy ? 'status-dot-green' : 'status-dot-red'} />
        {healthy ? t('module.online') : t('module.offline')}
      </span>
    </div>
  );
}

// =============================================================================
// Quick Links
// =============================================================================

function QuickLink({ to, label, icon }: { to: string; label: string; icon: React.ReactNode }) {
  return (
    <Link
      to={to}
      className="flex items-center gap-3 p-3 rounded-lg border border-gray-200
        hover:bg-primary-50 hover:border-primary-200 transition-all duration-150 group"
    >
      <span className="text-primary-500 group-hover:text-primary-600 transition-colors">
        {icon}
      </span>
      <span className="text-sm font-medium text-gray-700 group-hover:text-primary-700">
        {label}
      </span>
    </Link>
  );
}

// =============================================================================
// Dashboard Page
// =============================================================================

export default function Dashboard() {
  const { language } = useUIStore();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [statsData, healthData] = await Promise.all([
          dashboardAPI.stats().catch(() => null),
          healthAPI.check().catch(() => null),
        ]);
        setStats(statsData);
        setHealth(healthData);
      } catch {
        // Use placeholder data if backend is not available
        setStats({
          total_patients: 0,
          total_variants: 0,
          total_reports: 0,
          total_treatments: 0,
          recent_patients: [],
          tier_distribution: { I: 0, II: 0, III: 0, IV: 0 },
          module_status: [],
        });
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const moduleNames = [
    'VEP Service',
    'Phenotype RAG',
    'Phenotype Score',
    'PPI Score',
    'Variant Rank',
    'Report Service',
    'PanCancerSystem',
  ];

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="skeleton h-8 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="skeleton h-28 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{t('dashboard.welcome')}</h1>
        <p className="text-sm text-gray-500 mt-1">{t('dashboard.subtitle')}</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label={t('dashboard.total_patients')}
          value={stats?.total_patients ?? '-'}
          icon={<UserIcon />}
          color="bg-blue-100 text-blue-600"
          to="/patients"
        />
        <StatCard
          label={t('dashboard.total_variants')}
          value={stats?.total_variants ?? '-'}
          icon={<DnaIcon />}
          color="bg-purple-100 text-purple-600"
          to="/variants"
        />
        <StatCard
          label={t('dashboard.total_reports')}
          value={stats?.total_reports ?? '-'}
          icon={<ReportIcon />}
          color="bg-green-100 text-green-600"
        />
        <StatCard
          label={t('dashboard.total_treatments')}
          value={stats?.total_treatments ?? '-'}
          icon={<TreatmentIcon />}
          color="bg-amber-100 text-amber-600"
        />
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Module Status */}
        <div className="card lg:col-span-1">
          <div className="card-header">
            <h2 className="font-semibold text-gray-900">{t('dashboard.module_status')}</h2>
            <span className="text-xs text-gray-400">
              {health ? `${health.modules.filter((m) => m.healthy).length}/${health.modules.length} online` : '-'}
            </span>
          </div>
          <div className="card-body">
            {health?.modules ? (
              <div className="space-y-1">
                {health.modules.map((mod) => (
                  <ModuleStatusRow key={mod.name} name={mod.name} healthy={mod.healthy} />
                ))}
              </div>
            ) : (
              <div className="space-y-1">
                {moduleNames.map((name) => (
                  <ModuleStatusRow key={name} name={name} healthy={false} />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Quick Links */}
        <div className="card lg:col-span-1">
          <div className="card-header">
            <h2 className="font-semibold text-gray-900">{t('dashboard.quick_links')}</h2>
          </div>
          <div className="card-body grid gap-2">
            <QuickLink to="/pipeline" label={t('dashboard.new_analysis')} icon={<PlayIcon />} />
            <QuickLink to="/patients" label={t('dashboard.browse_patients')} icon={<SearchIcon />} />
          </div>
        </div>

        {/* Tier Distribution */}
        <div className="card lg:col-span-1">
          <div className="card-header">
            <h2 className="font-semibold text-gray-900">{t('dashboard.tier_distribution')}</h2>
          </div>
          <div className="card-body">
            {stats?.tier_distribution ? (
              <div className="space-y-3">
                {(['I', 'II', 'III', 'IV'] as const).map((tier) => {
                  const count = stats.tier_distribution[tier];
                  const total = Object.values(stats.tier_distribution).reduce((a, b) => a + b, 0) || 1;
                  const pct = Math.round((count / total) * 100);
                  const colors: Record<string, string> = {
                    I: 'bg-tier-1',
                    II: 'bg-tier-2',
                    III: 'bg-tier-3',
                    IV: 'bg-tier-4',
                  };
                  return (
                    <div key={tier} className="flex items-center gap-3">
                      <span className="badge text-xs w-8 justify-center"
                        style={{ backgroundColor: `var(--tw-${colors[tier].replace('bg-', '')})` }}
                      >
                        {tier}
                      </span>
                      <div className="flex-1 bg-gray-100 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full transition-all duration-500 ${colors[tier]}`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500 w-8 text-right">{count}</span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-gray-400">{t('common.no_data')}</p>
            )}
          </div>
        </div>
      </div>

      {/* Recent Patients */}
      {stats?.recent_patients && stats.recent_patients.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2 className="font-semibold text-gray-900">{t('dashboard.recent_patients')}</h2>
            <Link to="/patients" className="text-sm text-primary-600 hover:text-primary-700">
              {t('nav.patients')} &rarr;
            </Link>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>{t('patient.code')}</th>
                  <th>{t('patient.diagnosis')}</th>
                  <th>{t('patient.stage')}</th>
                  <th>{t('patient.created')}</th>
                </tr>
              </thead>
              <tbody>
                {stats.recent_patients.map((patient) => (
                  <tr key={patient.id}>
                    <td>
                      <Link to={`/patients/${patient.id}`} className="text-primary-600 hover:underline font-medium">
                        {patient.patient_code}
                      </Link>
                    </td>
                    <td className="text-gray-600">{patient.diagnosis}</td>
                    <td>
                      {patient.stage ? (
                        <span className="badge-blue">{patient.stage}</span>
                      ) : '-'}
                    </td>
                    <td className="text-gray-500 text-xs">
                      {patient.created_at ? new Date(patient.created_at).toLocaleDateString() : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Inline Icons
// =============================================================================

function UserIcon() {
  return (
    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
    </svg>
  );
}

function DnaIcon() {
  return (
    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
    </svg>
  );
}

function ReportIcon() {
  return (
    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  );
}

function TreatmentIcon() {
  return (
    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
    </svg>
  );
}

function PlayIcon() {
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
  );
}
