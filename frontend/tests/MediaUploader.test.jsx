import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import MediaUploader, { validateFile } from '../src/components/media/MediaUploader.jsx';

/**
 * Stub XMLHttpRequest so the uploader's real fetch path doesn't fire
 * during tests. We don't actually exercise the upload here — we only
 * assert on the DOM-level behaviour (dropzone renders, oversize files
 * fail validation with friendly errors).
 */
class FakeXHR {
  constructor() {
    this.upload = {};
    this.onload = null;
    this.onerror = null;
    this.onabort = null;
    this.responseText = '{}';
    this.status = 200;
  }
  open() {}
  setRequestHeader() {}
  send() {
    // never actually resolves -- we only test the queued state
  }
}

beforeEach(() => {
  vi.stubGlobal('XMLHttpRequest', FakeXHR);
});
afterEach(() => {
  vi.unstubAllGlobals();
});

describe('MediaUploader', () => {
  it('renders the dropzone and supported-types hint', () => {
    render(<MediaUploader athleteId="abc" />);
    expect(screen.getByTestId('dropzone')).toBeInTheDocument();
    expect(screen.getByText(/Drop files here or click to select/i)).toBeInTheDocument();
    // Hint mentions video size limit
    expect(screen.getByText(/500/)).toBeInTheDocument();
  });

  it('rejects oversize image files with a friendly error', () => {
    render(<MediaUploader athleteId="abc" />);
    const input = screen.getByTestId('file-input');

    // 12 MB image -> exceeds 10 MB image limit
    const big = new File([new Uint8Array(12 * 1024 * 1024)], 'huge.png', { type: 'image/png' });
    Object.defineProperty(input, 'files', { value: [big], configurable: true });
    fireEvent.change(input);

    const item = screen.getByTestId('upload-item');
    expect(item).toHaveAttribute('data-status', 'failed');
    const alert = within(item).getByRole('alert');
    expect(alert.textContent).toMatch(/too large/i);
    expect(alert.textContent).toMatch(/image/i);
  });

  it('rejects unsupported extensions with a friendly error', () => {
    render(<MediaUploader athleteId="abc" />);
    const input = screen.getByTestId('file-input');

    const exe = new File([new Uint8Array(1024)], 'evil.exe', { type: 'application/octet-stream' });
    Object.defineProperty(input, 'files', { value: [exe], configurable: true });
    fireEvent.change(input);

    const item = screen.getByTestId('upload-item');
    expect(item).toHaveAttribute('data-status', 'failed');
    expect(within(item).getByRole('alert').textContent).toMatch(/unsupported/i);
  });
});

describe('validateFile', () => {
  it('accepts a small jpg', () => {
    const f = new File([new Uint8Array(1024)], 'pic.jpg', { type: 'image/jpeg' });
    const r = validateFile(f);
    expect(r.ok).toBe(true);
    expect(r.category).toBe('image');
  });

  it('rejects oversized video', () => {
    // Use a sparse Blob so we don't actually allocate 600 MB.
    const f = new File([new Blob([])], 'movie.mp4', { type: 'video/mp4' });
    Object.defineProperty(f, 'size', { value: 600 * 1024 * 1024, configurable: true });
    const r = validateFile(f);
    expect(r.ok).toBe(false);
    expect(r.message).toMatch(/too large/i);
  });
});
