import { Search } from 'lucide-react';

/**
 * SearchBar — minimal stub by Agent 1.
 */
export default function SearchBar({ value = '', onChange = () => {}, placeholder = 'Search…' }) {
  return (
    <div
      style={{
        position: 'relative',
        display: 'flex',
        alignItems: 'center',
        width: '100%',
      }}
    >
      <Search
        size={14}
        style={{
          position: 'absolute',
          left: 12,
          color: 'var(--fg-tertiary)',
          pointerEvents: 'none',
        }}
      />
      <input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        style={{
          width: '100%',
          padding: '9px 12px 9px 32px',
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-md)',
          fontSize: 13,
          color: 'var(--fg-primary)',
          outline: 'none',
          transition: 'border-color var(--transition)',
        }}
        onFocus={(e) => (e.target.style.borderColor = 'var(--navy-500)')}
        onBlur={(e) => (e.target.style.borderColor = 'var(--border-default)')}
      />
    </div>
  );
}
