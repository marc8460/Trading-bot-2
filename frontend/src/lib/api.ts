/**
 * PropOS — API Client
 * Centralized API communication with the backend.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${endpoint}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// ─── Dashboard ───────────────────────────────

export const api = {
  dashboard: {
    getOverview: () => request<any>('/api/dashboard/overview'),
    getAccounts: () => request<any>('/api/dashboard/accounts'),
    getStrategy: () => request<any>('/api/dashboard/strategy'),
  },

  controls: {
    start: () => request<any>('/api/controls/start', { method: 'POST' }),
    stop: () => request<any>('/api/controls/stop', { method: 'POST' }),
    activateKillSwitch: (reason: string) =>
      request<any>('/api/controls/kill-switch/activate', {
        method: 'POST',
        body: JSON.stringify({ reason }),
      }),
    deactivateKillSwitch: () =>
      request<any>('/api/controls/kill-switch/deactivate', { method: 'POST' }),
    getKillSwitchStatus: () => request<any>('/api/controls/kill-switch/status'),
  },

  health: {
    check: () => request<any>('/api/health'),
  },
};
