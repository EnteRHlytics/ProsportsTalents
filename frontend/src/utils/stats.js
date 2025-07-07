export function computeSeasonData(summary) {
  const seasons = Object.keys(summary || {}).sort();
  const columns = new Set();
  seasons.forEach((season) => {
    const stats = summary[season] || {};
    Object.keys(stats).forEach((name) => columns.add(name));
  });
  const cols = Array.from(columns);
  const highs = {};
  cols.forEach((name) => {
    let max = -Infinity;
    seasons.forEach((season) => {
      const value = parseFloat(summary[season][name]);
      if (!isNaN(value) && value > max) {
        max = value;
      }
    });
    highs[name] = max;
  });
  return { seasons, columns: cols, highs };
}
