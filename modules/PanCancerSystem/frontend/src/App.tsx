import { Routes, Route, NavLink } from 'react-router-dom';
import { useUIStore } from '@/store';
import { t } from '@/i18n';

// Pages
import Dashboard from '@/pages/Dashboard';
import PatientList from '@/pages/PatientList';
import PatientDetail from '@/pages/PatientDetail';
import VariantBrowser from '@/pages/VariantBrowser';
import ReportView from '@/pages/ReportView';
import Settings from '@/pages/Settings';
import PipelineRun from '@/pages/PipelineRun';

// =============================================================================
// Navigation items
// =============================================================================

const navItems = [
  { path: '/', label: 'nav.dashboard', icon: DashboardIcon },
  { path: '/patients', label: 'nav.patients', icon: PatientsIcon },
  { path: '/variants', label: 'nav.variants', icon: VariantsIcon },
  { path: '/pipeline', label: 'nav.pipeline', icon: PipelineIcon },
  { path: '/settings', label: 'nav.settings', icon: SettingsIcon },
];

// =============================================================================
// Sidebar
// =============================================================================

function Sidebar() {
  const { sidebarOpen, language, setLanguage } = useUIStore();

  return (
    <aside
      className={`fixed left-0 top-0 z-40 h-screen bg-white border-r border-gray-200
        transition-all duration-300 ease-in-out flex flex-col
        ${sidebarOpen ? 'w-64' : 'w-16'}`}
    >
      {/* Logo */}
      <div className="flex items-center h-16 px-4 border-b border-gray-100">
        <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center flex-shrink-0">
          <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
        </div>
        {sidebarOpen && (
          <span className="ml-3 text-lg font-bold text-gray-900 whitespace-nowrap">
            OpenPanCan
          </span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium
              transition-colors duration-150
              ${isActive
                ? 'bg-primary-50 text-primary-700'
                : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              }
              ${!sidebarOpen && 'justify-center'}`
            }
            title={t(item.label, language)}
          >
            <item.icon />
            {sidebarOpen && <span>{t(item.label, language)}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Language toggle */}
      <div className="p-2 border-t border-gray-100">
        <button
          onClick={() => setLanguage(language === 'en' ? 'zh' : 'en')}
          className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm
            text-gray-600 hover:bg-gray-100 transition-colors
            ${!sidebarOpen && 'justify-center'}`}
        >
          <span className="text-base">{language === 'en' ? '🇨🇳' : '🇺🇸'}</span>
          {sidebarOpen && (
            <span>{language === 'en' ? '中文' : 'English'}</span>
          )}
        </button>
      </div>
    </aside>
  );
}

// =============================================================================
// Header
// =============================================================================

function Header() {
  const { sidebarOpen, toggleSidebar } = useUIStore();

  return (
    <header className="sticky top-0 z-30 h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      <button
        onClick={toggleSidebar}
        className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 transition-colors"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <div className="flex items-center gap-4">
        {/* System status */}
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <span className="status-dot-green" />
          <span className="hidden sm:inline">System Online</span>
        </div>

        {/* User avatar placeholder */}
        <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-sm font-medium">
          OC
        </div>
      </div>
    </header>
  );
}

// =============================================================================
// App Layout
// =============================================================================

function AppLayout({ children }: { children: React.ReactNode }) {
  const { sidebarOpen } = useUIStore();

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      <div className={`transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-16'}`}>
        <Header />
        <main className="p-6 animate-fade-in">
          {children}
        </main>
      </div>
    </div>
  );
}

// =============================================================================
// Main App
// =============================================================================

export default function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/patients" element={<PatientList />} />
        <Route path="/patients/:id" element={<PatientDetail />} />
        <Route path="/variants/:patientId?" element={<VariantBrowser />} />
        <Route path="/reports/:patientId?" element={<ReportView />} />
        <Route path="/pipeline" element={<PipelineRun />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </AppLayout>
  );
}

// =============================================================================
// SVG Icon Components (inline for zero-dependency)
// =============================================================================

function DashboardIcon() {
  return (
    <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1h-2z" />
    </svg>
  );
}

function PatientsIcon() {
  return (
    <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  );
}

function VariantsIcon() {
  return (
    <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  );
}

function PipelineIcon() {
  return (
    <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  );
}

function SettingsIcon() {
  return (
    <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  );
}
