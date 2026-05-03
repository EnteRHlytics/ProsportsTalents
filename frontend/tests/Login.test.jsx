import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import Login from '../src/views/Login.jsx';

// Mock useAuth so the component renders without a live AuthProvider.
const mockLogin = vi.fn();
vi.mock('../src/context/AuthContext', () => ({
  useAuth: () => ({
    user: null,
    login: mockLogin,
    refresh: vi.fn(),
  }),
}));

describe('Login view', () => {
  it('renders three SSO buttons (Google, GitHub, Microsoft) and triggers provider login', async () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );

    const google = screen.getByRole('button', { name: /Continue with Google/i });
    const github = screen.getByRole('button', { name: /Continue with GitHub/i });
    const microsoft = screen.getByRole('button', { name: /Continue with Microsoft/i });

    expect(google).toBeInTheDocument();
    expect(github).toBeInTheDocument();
    expect(microsoft).toBeInTheDocument();

    await userEvent.click(google);
    expect(mockLogin).toHaveBeenCalledWith('google');

    await userEvent.click(github);
    expect(mockLogin).toHaveBeenCalledWith('github');

    await userEvent.click(microsoft);
    expect(mockLogin).toHaveBeenCalledWith('microsoft');
  });

  it('shows email/password fallback form', () => {
    const { container } = render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );
    expect(container.querySelector('input[autocomplete="username"]')).toBeInTheDocument();
    expect(container.querySelector('input[autocomplete="current-password"]')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Sign in$/i })).toBeInTheDocument();
  });
});
