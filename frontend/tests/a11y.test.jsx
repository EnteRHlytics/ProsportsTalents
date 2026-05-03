import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import axe from 'axe-core';

// --- Mocks -----------------------------------------------------------------
// Mock useApi so the Dashboard never actually fetches in jsdom. Returns
// a stable shape: { data, error, loading, refetch }.
vi.mock('../src/hooks/useApi', () => {
  const useApi = vi.fn(() => ({
    data: { total: 0, results: [] },
    error: null,
    loading: false,
    refetch: vi.fn(),
  }));
  return { default: useApi, apiFetch: vi.fn() };
});

// Mock AuthContext so we don't need to wire its provider with real state.
vi.mock('../src/context/AuthContext', () => ({
  useAuth: () => ({ user: null, isAuthenticated: false }),
  AuthProvider: ({ children }) => children,
}));

// Stub fetch defensively in case any dependency probes the network.
vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({
  ok: true,
  status: 200,
  json: () => Promise.resolve({ total: 0, results: [] }),
  text: () => Promise.resolve('{"total":0,"results":[]}'),
})));

// Import the Dashboard *after* mocks are registered.
import Dashboard from '../src/views/Dashboard';

describe('a11y: Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('has no critical accessibility violations', async () => {
    const { container } = render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    // Run axe-core directly against the rendered DOM. Filter to serious/critical
    // so we surface only the most egregious WCAG issues.
    const results = await axe.run(container, {
      runOnly: {
        type: 'tag',
        values: ['wcag2a', 'wcag2aa'],
      },
      // color-contrast can produce false positives in jsdom (no real layout/colours),
      // and document-title / region run on the full document, not a fragment.
      rules: {
        'color-contrast': { enabled: false },
        'document-title': { enabled: false },
        'html-has-lang': { enabled: false },
        'landmark-one-main': { enabled: false },
        'region': { enabled: false },
        'page-has-heading-one': { enabled: false },
      },
    });

    const seriousViolations = results.violations.filter(
      v => v.impact === 'serious' || v.impact === 'critical'
    );

    if (seriousViolations.length > 0) {
      // Surface details for debugging when this fails in CI.
      // eslint-disable-next-line no-console
      console.error(
        'a11y violations:',
        seriousViolations.map(v => ({
          id: v.id,
          impact: v.impact,
          help: v.help,
          nodes: v.nodes.length,
        }))
      );
    }

    expect(seriousViolations).toEqual([]);
  });
});
