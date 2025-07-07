import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import SeasonStats from '../src/components/SeasonStats.jsx';

vi.stubGlobal('fetch', vi.fn());

const summary = {
  '2022': { points: '10', rebounds: '5' },
  '2023': { points: '15', rebounds: '7' }
};

function mockSummary() {
  fetch.mockResolvedValueOnce({
    ok: true,
    json: () => Promise.resolve(summary)
  });
}

describe('SeasonStats', () => {
  it('renders stats table with career highs highlighted', async () => {
    mockSummary();
    render(<SeasonStats athleteId="1" />);
    await waitFor(() => screen.getByText('Season Totals'));
    expect(screen.getByText('2022')).toBeInTheDocument();
    expect(screen.getByText('2023')).toBeInTheDocument();
    const highCell = screen.getAllByText('15')[0];
    expect(highCell.classList.contains('career-high')).toBe(true);
  });
});
