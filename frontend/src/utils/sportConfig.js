/**
 * sportConfig — colors, labels, default stat columns per sport.
 * Minimal stub by Agent 1 to satisfy existing imports.
 */
const CONFIGS = {
  NBA: { code: 'NBA', label: 'Basketball',  color: '#f07a28', accent: '#f9bb89' },
  NFL: { code: 'NFL', label: 'Football',    color: '#2ea65c', accent: '#7cd49a' },
  MLB: { code: 'MLB', label: 'Baseball',    color: '#1f7db0', accent: '#7ab8d6' },
  NHL: { code: 'NHL', label: 'Hockey',      color: '#9b6dd2', accent: '#c4a8e6' },
  SOC: { code: 'SOC', label: 'Soccer',      color: '#22a08c', accent: '#74cdba' },
};

const DEFAULT = { code: 'GEN', label: 'Sport', color: '#2d6489', accent: '#7aaabb' };

export function getSportConfig(code) {
  if (!code) return DEFAULT;
  return CONFIGS[String(code).toUpperCase()] || DEFAULT;
}

export function listSports() {
  return Object.values(CONFIGS);
}

export default getSportConfig;
