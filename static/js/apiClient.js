export async function fetchWithRetry(url, options = {}, retries = 3) {
  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      const res = await fetch(url, options);
      if (!res.ok) throw new Error('Request failed');
      return await res.json();
    } catch (err) {
      if (attempt === retries - 1) throw err;
      await new Promise(r => setTimeout(r, 500 * (attempt + 1)));
    }
  }
}

const cache = new Map();

export async function getAthlete(id) {
  if (cache.has(id)) return cache.get(id);
  const data = await fetchWithRetry(`/api/athletes/${id}`);
  cache.set(id, data);
  return data;
}
