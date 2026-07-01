// =============================================================================
// OpenPanCan - Zustand Store
// =============================================================================

import { create } from 'zustand';
import type { CancerPatient, DashboardStats, SystemHealth } from '@/types';

// ---------------------------------------------------------------------------
// Auth Store
// ---------------------------------------------------------------------------

interface AuthState {
  /** Whether the user is authenticated */
  isAuthenticated: boolean;
  /** Current user display name */
  userName: string;
  /** Login action */
  login: (name: string) => void;
  /** Logout action */
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: true, // No auth required for now — open system
  userName: 'Clinician',
  login: (name: string) => set({ isAuthenticated: true, userName: name }),
  logout: () => set({ isAuthenticated: false, userName: '' }),
}));

// ---------------------------------------------------------------------------
// Selected Patient Store
// ---------------------------------------------------------------------------

interface PatientState {
  /** Currently selected patient */
  selectedPatient: CancerPatient | null;
  /** Patient list */
  patients: CancerPatient[];
  /** Loading state */
  loading: boolean;
  /** Error state */
  error: string | null;
  /** Set the selected patient */
  selectPatient: (patient: CancerPatient | null) => void;
  /** Set the patient list */
  setPatients: (patients: CancerPatient[]) => void;
  /** Set loading */
  setLoading: (loading: boolean) => void;
  /** Set error */
  setError: (error: string | null) => void;
}

export const usePatientStore = create<PatientState>((set) => ({
  selectedPatient: null,
  patients: [],
  loading: false,
  error: null,
  selectPatient: (patient) => set({ selectedPatient: patient }),
  setPatients: (patients) => set({ patients }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}));

// ---------------------------------------------------------------------------
// Dashboard Store
// ---------------------------------------------------------------------------

interface DashboardState {
  stats: DashboardStats | null;
  loading: boolean;
  error: string | null;
  setStats: (stats: DashboardStats) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  stats: null,
  loading: false,
  error: null,
  setStats: (stats) => set({ stats }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}));

// ---------------------------------------------------------------------------
// System Health Store
// ---------------------------------------------------------------------------

interface HealthState {
  health: SystemHealth | null;
  lastChecked: string | null;
  loading: boolean;
  setHealth: (health: SystemHealth) => void;
  setLoading: (loading: boolean) => void;
}

export const useHealthStore = create<HealthState>((set) => ({
  health: null,
  lastChecked: null,
  loading: false,
  setHealth: (health) =>
    set({ health, lastChecked: new Date().toISOString() }),
  setLoading: (loading) => set({ loading }),
}));

// ---------------------------------------------------------------------------
// UI Store
// ---------------------------------------------------------------------------

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  language: 'en' | 'zh';
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setLanguage: (lang: 'en' | 'zh') => void;
  setTheme: (theme: 'light' | 'dark') => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  theme: 'light',
  language: 'en',
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setLanguage: (language) => set({ language }),
  setTheme: (theme) => set({ theme }),
}));
