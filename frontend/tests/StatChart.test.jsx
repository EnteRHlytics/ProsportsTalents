import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import StatChart from '../src/components/StatChart.jsx';

vi.mock('react-chartjs-2', () => ({
  Line: ({ data }) => <div data-testid="chart">{JSON.stringify(data)}</div>
}));

vi.stubGlobal('fetch', vi.fn());

const summary = {
  '2022': { points: '10' },
  '2023': { points: '15' }
};

function mockSummary() {
  fetch.mockResolvedValueOnce({
    ok: true,
    json: () => Promise.resolve(summary)
  });
}

describe('StatChart', () => {
  it('plots data points for selected stat', async () => {
    mockSummary();
    render(<StatChart athleteId="1" />);
    await waitFor(() => screen.getByTestId('chart'));
    const chart = screen.getByTestId('chart');
    const chartData = JSON.parse(chart.textContent);
    expect(chartData.labels).toEqual(['2022', '2023']);
    expect(chartData.datasets[0].data).toEqual([10, 15]);
  });
});
