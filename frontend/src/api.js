// API client - Sports Betting Analytics
// Mode hybride : essaie d'abord l'API live, fallback sur data.json statique
const API_BASE = window.API_BASE || "http://localhost:8000";

let _staticData = null;
async function loadStatic() {
  if (_staticData) return _staticData;
  try {
    const res = await fetch("./data.json");
    _staticData = await res.json();
    return _staticData;
  } catch (e) {
    return null;
  }
}

async function tryApi(path) {
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 1500);
    const res = await fetch(`${API_BASE}${path}`, { signal: ctrl.signal });
    clearTimeout(t);
    if (!res.ok) throw new Error("API error");
    return res.json();
  } catch (e) {
    return null;
  }
}

window.api = {
  async matches() {
    const live = await tryApi("/api/matches");
    if (live) return live;
    const data = await loadStatic();
    return data ? data.matches_summary : [];
  },
  async match(id) {
    const live = await tryApi(`/api/matches/${id}`);
    if (live) return live;
    const data = await loadStatic();
    return data ? data.matches_full[id] : null;
  },
  async teams() {
    const live = await tryApi("/api/teams");
    if (live) return live;
    const data = await loadStatic();
    return data ? data.teams : [];
  },
  async valueBets(minEdge = 5) {
    const live = await tryApi(`/api/value-bets?min_edge=${minEdge}`);
    if (live) return live;
    const data = await loadStatic();
    if (!data) return [];
    return data.value_bets.filter(b => b.edge_pct >= minEdge);
  },
};
