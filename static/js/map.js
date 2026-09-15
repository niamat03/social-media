(function () {
  const mapEl = document.getElementById('map');
  if (!mapEl) return;

  const statusEl = document.getElementById('map-status');
  const radiusSelect = document.getElementById('radius-select');
  const scopeSelect = document.getElementById('scope-select');

  const map = L.map('map').setView([31.6295, -7.9811], 6); // Morocco-ish default center
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
    maxZoom: 18,
  }).addTo(map);

  const markers = L.markerClusterGroup();
  map.addLayer(markers);

  let currentCenter = null;

  function popupHtml(props) {
    return `
      <div style="min-width:180px">
        <strong>${escapeHtml(props.author)}</strong><br>
        <span style="font-size:0.85em;color:#666">${escapeHtml(props.created_at)}${props.city ? ' · ' + escapeHtml(props.city) : ''}</span>
        <p style="margin:6px 0">${escapeHtml(props.content)}</p>
        <span style="font-size:0.85em;display:inline-flex;align-items:center;gap:10px;color:#444">
          <span style="display:inline-flex;align-items:center;gap:3px;"><svg class="icon icon-sm"><use href="#icon-heart"></use></svg> ${props.like_count}</span>
          <span style="display:inline-flex;align-items:center;gap:3px;"><svg class="icon icon-sm"><use href="#icon-message-circle"></use></svg> ${props.comment_count}</span>
        </span><br>
        <a href="${props.url}" style="color:#1877f2;font-weight:600;">View post</a>
      </div>
    `;
  }

  async function loadNearby(lat, lng) {
    currentCenter = { lat, lng };
    const radius = radiusSelect ? radiusSelect.value : 5;
    const scope = scopeSelect ? scopeSelect.value : 'all';
    statusEl.textContent = 'Loading nearby posts...';

    try {
      const data = await apiGet(`/geo/api/posts/nearby/?lat=${lat}&lng=${lng}&radius=${radius}&scope=${scope}`);
      markers.clearLayers();

      if (data.features.length === 0) {
        statusEl.textContent = scope === 'following'
          ? 'None of the people you follow have posted nearby. Try "Everyone" or a bigger radius.'
          : 'No posts nearby yet. Try expanding your search radius.';
      } else {
        statusEl.textContent = `${data.features.length} post(s) found within ${radius} km.`;
      }

      data.features.forEach((feature) => {
        const [lngC, latC] = feature.geometry.coordinates;
        const marker = L.marker([latC, lngC]);
        marker.bindPopup(popupHtml(feature.properties));
        markers.addLayer(marker);
      });
    } catch (err) {
      statusEl.textContent = 'Could not load nearby posts.';
      console.error(err);
    }
  }

  if (radiusSelect) {
    radiusSelect.addEventListener('change', () => {
      if (currentCenter) loadNearby(currentCenter.lat, currentCenter.lng);
    });
  }

  if (scopeSelect) {
    scopeSelect.addEventListener('change', () => {
      if (currentCenter) loadNearby(currentCenter.lat, currentCenter.lng);
    });
  }

  const locateBtn = document.getElementById('locate-btn');
  function useLocation(lat, lng, zoom) {
    map.setView([lat, lng], zoom || 12);
    L.marker([lat, lng], { title: 'You are here' }).addTo(map);
    loadNearby(lat, lng);
  }

  if (locateBtn) {
    locateBtn.addEventListener('click', () => {
      if (!navigator.geolocation) {
        statusEl.textContent = 'Geolocation is not available on this device.';
        return;
      }
      statusEl.textContent = 'Requesting your location...';
      navigator.geolocation.getCurrentPosition(
        (position) => useLocation(position.coords.latitude, position.coords.longitude),
        () => {
          statusEl.textContent = 'Location permission denied. Use the search box instead.';
        }
      );
    });
  }

  map.on('click', (event) => {
    useLocation(event.latlng.lat, event.latlng.lng, map.getZoom());
  });

  const searchInput = document.getElementById('location-search-input');
  const searchBtn = document.getElementById('location-search-btn');
  const searchResults = document.getElementById('location-search-results');

  async function runLocationSearch() {
    const query = searchInput.value.trim();
    if (!query) return;

    searchResults.hidden = false;
    searchResults.innerHTML = '<div class="location-search-result">Searching…</div>';

    try {
      const data = await apiGet(`/geo/api/search-location/?q=${encodeURIComponent(query)}`);
      searchResults.innerHTML = '';

      if (!data.results.length) {
        searchResults.innerHTML = '<div class="location-search-result">No matching place found.</div>';
        return;
      }

      data.results.forEach((place) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'location-search-result';
        btn.textContent = place.display_name;
        btn.addEventListener('click', () => {
          searchResults.hidden = true;
          searchInput.value = place.display_name;
          useLocation(place.lat, place.lon, 12);
        });
        searchResults.appendChild(btn);
      });
    } catch (err) {
      searchResults.innerHTML = '<div class="location-search-result">Search failed. Try again.</div>';
      console.error(err);
    }
  }

  if (searchBtn) {
    searchBtn.addEventListener('click', runLocationSearch);
  }
  if (searchInput) {
    searchInput.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        runLocationSearch();
      }
    });
    document.addEventListener('click', (event) => {
      if (!event.target.closest('.location-search')) {
        searchResults.hidden = true;
      }
    });
  }
})();
