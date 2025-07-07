import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import GameLog from '../src/components/GameLog.jsx';

vi.stubGlobal('fetch', vi.fn());

const summary = { '2023': {} };
const page1 = { items: [
  { game_id: 1, date: '2023-01-01', opponent_name: 'A', home_team_score: 1, visitor_team_score: 0 }
], total: 6 };
const page2 = { items: [
  { game_id: 2, date: '2023-01-02', opponent_name: 'B', home_team_score: 2, visitor_team_score: 3 }
], total: 6 };

function queueResponses() {
  fetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(summary) });
  fetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(page1) });
  fetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(page2) });
}

describe('GameLog', () => {
  it('paginates through games', async () => {
    queueResponses();
    render(<GameLog athleteId="1" />);
    await waitFor(() => screen.getByText('A'));
    expect(screen.getByText('1 / 2')).toBeInTheDocument();

    await userEvent.click(screen.getByText('Next'));
    await waitFor(() => screen.getByText('B'));
    expect(screen.getByText('2 / 2')).toBeInTheDocument();
  });
});
