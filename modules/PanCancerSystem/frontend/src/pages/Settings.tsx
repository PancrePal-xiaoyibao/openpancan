import { useState } from 'react';
import { useUIStore } from '@/store';
import { t, setLanguage } from '@/i18n';

// =============================================================================
// Settings Section
// =============================================================================

function SettingsSection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="card">
      <div className="card-header">
        <h3 className="font-semibold text-gray-900">{title}</h3>
      </div>
      <div className="card-body space-y-4">{children}</div>
    </div>
  );
}

// =============================================================================
// Settings Page
// =============================================================================

export default function Settings() {
  const { language, theme, setTheme } = useUIStore();

  const [settings, setSettings] = useState({
    apiBaseUrl: '/api',
    defaultPageSize: '20',
    autoRefresh: true,
    refreshInterval: '30',
    enableNotifications: true,
  });

  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    // In production, this would persist to the backend
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleLanguageChange = (lang: 'en' | 'zh') => {
    setLanguage(lang);
    useUIStore.getState().setLanguage(lang);
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{t('settings.title')}</h1>
        <p className="text-sm text-gray-500 mt-1">Configure system preferences</p>
      </div>

      {/* Appearance */}
      <SettingsSection title={t('settings.appearance')}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-900">{t('settings.language')}</p>
            <p className="text-xs text-gray-500">Select interface language</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => handleLanguageChange('en')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors
                ${language === 'en'
                  ? 'bg-primary-100 text-primary-700 border border-primary-300'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
            >
              English
            </button>
            <button
              onClick={() => handleLanguageChange('zh')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors
                ${language === 'zh'
                  ? 'bg-primary-100 text-primary-700 border border-primary-300'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
            >
              中文
            </button>
          </div>
        </div>

        <div className="divider" />

        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-900">Theme</p>
            <p className="text-xs text-gray-500">Choose between light and dark mode</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setTheme('light')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors
                ${theme === 'light'
                  ? 'bg-primary-100 text-primary-700 border border-primary-300'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
            >
              ☀️ Light
            </button>
            <button
              onClick={() => setTheme('dark')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors
                ${theme === 'dark'
                  ? 'bg-primary-100 text-primary-700 border border-primary-300'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
            >
              🌙 Dark
            </button>
          </div>
        </div>
      </SettingsSection>

      {/* API Configuration */}
      <SettingsSection title={t('settings.api')}>
        <div>
          <label className="label">API Base URL</label>
          <input
            className="input"
            value={settings.apiBaseUrl}
            onChange={(e) => setSettings({ ...settings, apiBaseUrl: e.target.value })}
          />
        </div>
      </SettingsSection>

      {/* Display Settings */}
      <SettingsSection title={t('settings.general')}>
        <div>
          <label className="label">Default Page Size</label>
          <select
            className="input"
            value={settings.defaultPageSize}
            onChange={(e) => setSettings({ ...settings, defaultPageSize: e.target.value })}
          >
            <option value="10">10</option>
            <option value="20">20</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </select>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-900">Auto-refresh Dashboard</p>
            <p className="text-xs text-gray-500">Automatically refresh dashboard data</p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.autoRefresh}
              onChange={(e) => setSettings({ ...settings, autoRefresh: e.target.checked })}
              className="sr-only peer"
            />
            <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary-600" />
          </label>
        </div>

        {settings.autoRefresh && (
          <div>
            <label className="label">Refresh Interval (seconds)</label>
            <input
              type="number"
              className="input"
              value={settings.refreshInterval}
              onChange={(e) => setSettings({ ...settings, refreshInterval: e.target.value })}
              min={5}
              max={300}
            />
          </div>
        )}

        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-900">Notifications</p>
            <p className="text-xs text-gray-500">Show pipeline completion notifications</p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.enableNotifications}
              onChange={(e) => setSettings({ ...settings, enableNotifications: e.target.checked })}
              className="sr-only peer"
            />
            <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary-600" />
          </label>
        </div>
      </SettingsSection>

      {/* Database Info */}
      <SettingsSection title={t('settings.database')}>
        <div className="flex items-center justify-between py-2">
          <span className="text-sm text-gray-500">Type</span>
          <span className="text-sm font-medium text-gray-900">SQLite</span>
        </div>
        <div className="flex items-center justify-between py-2">
          <span className="text-sm text-gray-500">Location</span>
          <span className="text-sm font-mono text-gray-700">/data/openpancan.db</span>
        </div>
        <div className="flex items-center justify-between py-2">
          <span className="text-sm text-gray-500">Status</span>
          <span className="flex items-center gap-1.5 text-sm text-green-700">
            <span className="status-dot-green" />
            Connected
          </span>
        </div>
      </SettingsSection>

      {/* Module Status */}
      <SettingsSection title={t('settings.modules')}>
        {[
          { name: 'VEP Service', port: 8001, status: 'online' },
          { name: 'Phenotype RAG', port: 8002, status: 'online' },
          { name: 'Phenotype Score', port: 8003, status: 'online' },
          { name: 'PPI Score', port: 8004, status: 'online' },
          { name: 'Variant Rank', port: 8005, status: 'online' },
          { name: 'Report Service', port: 8006, status: 'online' },
          { name: 'PanCancerSystem', port: 8007, status: 'online' },
        ].map((mod) => (
          <div key={mod.name} className="flex items-center justify-between py-2">
            <div className="flex items-center gap-3">
              <span className={mod.status === 'online' ? 'status-dot-green' : 'status-dot-red'} />
              <span className="text-sm text-gray-700">{mod.name}</span>
            </div>
            <span className="text-xs text-gray-400 font-mono">:{mod.port}</span>
          </div>
        ))}
      </SettingsSection>

      {/* Save button */}
      <div className="flex items-center gap-4">
        <button onClick={handleSave} className="btn-primary">
          {t('common.save')}
        </button>
        {saved && (
          <span className="text-sm text-green-600 animate-fade-in">{t('settings.save_success')}</span>
        )}
      </div>

      {/* Footer */}
      <div className="text-center text-xs text-gray-400 pb-8">
        OpenPanCan v0.1.0 — Pancreatic Cancer Genomic Analysis System
      </div>
    </div>
  );
}
