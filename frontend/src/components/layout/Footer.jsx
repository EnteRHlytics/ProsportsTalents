import { Trophy, Github, Mail } from 'lucide-react';

export default function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer
      style={{
        background: 'var(--bg-footer)',
        borderTop: '1px solid var(--border-subtle)',
        color: 'var(--fg-tertiary)',
        marginTop: 32,
      }}
    >
      <div
        style={{
          maxWidth: 1280,
          margin: '0 auto',
          padding: '24px clamp(16px, 4vw, 32px)',
          display: 'flex',
          flexWrap: 'wrap',
          gap: 24,
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Trophy size={16} color="var(--orange-500)" />
          <span style={{ color: 'var(--fg-secondary)', fontSize: 13, fontWeight: 600 }}>
            ProsportsTalents
          </span>
          <span style={{ fontSize: 12 }}>© {year}</span>
        </div>

        <nav style={{ display: 'flex', gap: 18, flexWrap: 'wrap' }}>
          <a href="/discover" style={{ fontSize: 13, color: 'var(--fg-tertiary)' }}>Athletes</a>
          <a href="/prospects" style={{ fontSize: 13, color: 'var(--fg-tertiary)' }}>Prospects</a>
          <a href="/compare" style={{ fontSize: 13, color: 'var(--fg-tertiary)' }}>Compare</a>
        </nav>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <a
            href="mailto:contact@prosportstalents.example"
            aria-label="Contact email"
            style={{ color: 'var(--fg-tertiary)' }}
            title="Contact"
          >
            <Mail size={16} />
          </a>
          <a
            href="https://github.com/"
            target="_blank"
            rel="noreferrer"
            aria-label="GitHub"
            style={{ color: 'var(--fg-tertiary)' }}
          >
            <Github size={16} />
          </a>
        </div>
      </div>
    </footer>
  );
}
