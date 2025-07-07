// Simple search form handler for the homepage

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('homepage-search');
  if (!form) return;

  const input = document.getElementById('search-query');
  const button = document.getElementById('search-submit');
  const results = document.getElementById('search-results');
  const tabs = document.querySelectorAll('#filter-tabs .nav-link');
  const featured = document.getElementById('featured-grid');
  const urlParams = new URLSearchParams(window.location.search);
  let activeFilter = urlParams.get('filter') || document.querySelector('#filter-tabs .nav-link.active')?.dataset.filter || '';
  if (urlParams.get('q')) {
    input.value = urlParams.get('q');
  }

  function updateURL() {
    const params = new URLSearchParams();
    const q = input.value.trim();
    if (q) params.set('q', q);
    if (activeFilter) params.set('filter', activeFilter);
    const newUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.replaceState({}, '', newUrl);
  }

  function createCard(ath) {
    const card = document.createElement('a');
    card.className = 'athlete-card card h-100 text-decoration-none';
    card.href = `/athletes/${ath.athlete_id}`;

    const body = document.createElement('div');
    body.className = 'card-body';

    const header = document.createElement('div');
    header.className = 'd-flex align-items-center mb-2';

    let photoEl;
    if (ath.profile_image_url) {
      photoEl = document.createElement('img');
      photoEl.className = 'athlete-photo me-2';
      photoEl.src = ath.profile_image_url;
      photoEl.alt = `${ath.user.full_name} photo`;
    } else {
      photoEl = document.createElement('div');
      photoEl.className = 'athlete-photo me-2';
      const initials = ath.user.full_name
        .split(/\s+/)
        .slice(0, 2)
        .map((n) => n[0])
        .join('')
        .toUpperCase();
      photoEl.textContent = initials;
    }

    const title = document.createElement('h5');
    title.className = 'card-title mb-0';
    title.textContent = ath.user.full_name;

    header.appendChild(photoEl);
    header.appendChild(title);

    const team = document.createElement('p');
    team.className = 'card-text';
    team.textContent = ath.current_team || 'N/A';

    const rating = document.createElement('p');
    rating.className = 'card-text';
    rating.innerHTML = `<small class="text-muted">Rating: ${ath.overall_rating ?? '-'}</small>`;

    body.appendChild(header);
    body.appendChild(team);
    body.appendChild(rating);
    card.appendChild(body);

    return card;
  }

  function debounce(fn, delay) {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), delay);
    };
  }

  async function runSearch(params) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    try {
      const res = await fetch(`/api/athletes/search?${params.toString()}`, {
        signal: controller.signal,
      });
      if (res.status === 429) {
        throw new Error('Rate limit exceeded');
      }
      if (!res.ok) {
        throw new Error('Request failed');
      }
      const data = await res.json();
      return data.results || [];
    } finally {
      clearTimeout(timeoutId);
    }
  }

  async function runFeatured(limit = 6) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    try {
      const res = await fetch(`/api/athletes/featured?limit=${limit}`, {
        signal: controller.signal,
      });
      if (!res.ok) {
        throw new Error('Request failed');
      }
      return await res.json();
    } finally {
      clearTimeout(timeoutId);
    }
  }

  async function updateFeatured() {
    if (!featured) return;
    const params = new URLSearchParams();
    const query = input.value.trim();
    let useSearch = true;
    if (query) params.append('q', query);
    if (activeFilter) {
      const f = activeFilter.toLowerCase();
      if (['nba', 'nfl', 'mlb', 'nhl'].includes(f)) {
        params.append('sport', f.toUpperCase());
      } else if (f === 'top' && !query) {
        useSearch = false;
      } else {
        params.append('filter', f);
      }
    } else if (!query) {
      useSearch = false;
    }
    featured.innerHTML = '';
    try {
      const athletes = useSearch ? await runSearch(params) : await runFeatured();
      if (athletes.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'text-center w-100';
        empty.textContent = 'No matching athletes found';
        featured.appendChild(empty);
        return;
      }
      athletes.forEach((ath) => {
        featured.appendChild(createCard(ath));
      });
    } catch (err) {
      const msg = document.createElement('div');
      msg.className = 'text-center text-danger w-100';
      if (err.message.includes('Rate limit')) {
        msg.textContent = 'Too many requests. Please slow down and try again.';
      } else if (err.name === 'AbortError') {
        msg.textContent = 'Request timed out. Please try again.';
      } else {
        msg.textContent = 'Error fetching athletes. Please try again.';
      }
      featured.appendChild(msg);
      throw err;
    }
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const original = button.textContent;
    button.textContent = 'Searching…';
    button.disabled = true;

    try {
      await updateFeatured();
      updateURL();
    } catch (err) {
      console.error('Search failed', err);
      alert('Search failed. Please try again.');
    } finally {
      button.textContent = original;
      button.disabled = false;
    }
  });

  const debouncedUpdateFeatured = debounce(updateFeatured, 300);

  tabs.forEach((tab) => {
    tab.addEventListener('click', (e) => {
      e.preventDefault();
      tabs.forEach((t) => t.classList.remove('active'));
      tab.classList.add('active');
      activeFilter = tab.dataset.filter;
      debouncedUpdateFeatured();
      updateURL();
    });
  });

  if (activeFilter) {
    tabs.forEach((t) => {
      if (t.dataset.filter === activeFilter) {
        tabs.forEach((el) => el.classList.remove('active'));
        t.classList.add('active');
      }
    });
  }

  if (urlParams.get('q') || activeFilter) {
    updateFeatured();
  }
});
