/**
 * PageWrapper — consistent max-width + padding container for app routes.
 * Used across discover/compare/prospect/profile pages.
 */
export default function PageWrapper({ children, maxWidth = 1200, style }) {
  return (
    <div
      style={{
        maxWidth,
        margin: '0 auto',
        padding: 'clamp(16px, 4vw, 32px)',
        width: '100%',
        ...style,
      }}
    >
      {children}
    </div>
  );
}
