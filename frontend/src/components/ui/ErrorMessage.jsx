/**
 * ErrorMessage — minimal stub by Agent 1 to satisfy existing imports.
 * Another agent will likely replace this with their own design.
 */
export default function ErrorMessage({ message }) {
  if (!message) return null;
  return (
    <div
      role="alert"
      style={{
        padding: '10px 14px',
        margin: '8px 0',
        background: 'rgba(240, 122, 40, 0.10)',
        border: '1px solid var(--orange-500)',
        borderRadius: 'var(--radius-md)',
        color: 'var(--orange-300)',
        fontSize: 13,
      }}
    >
      {message}
    </div>
  );
}
