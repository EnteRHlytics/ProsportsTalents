document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('customize-metrics-btn');
  if (btn) {
    new bootstrap.Tooltip(btn);
  }
});
