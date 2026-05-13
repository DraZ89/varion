// ========== HOME PAGE - Multi-sports unifie ==========
// Affiche tous les matchs du jour (foot + tennis), tries par heure de debut

const { useState: useStateH, useEffect: useEffectH } = React;


// Helper : calculer un timestamp pour le tri unifie
function getMatchTimestamp(match, sport) {
  // Priorite : timestamp Unix UTC fiable
  if (match.start_timestamp_ms && match.start_timestamp_ms > 0) {
    return match.start_timestamp_ms;
  }
  if (match.startTimestamp && match.startTimestamp > 0) {
    return match.startTimestamp * 1000;  // foot SportAPI7 (sec)
  }
  // Fallback : parsing date + time
  const date = match.date || "";
  const time = sport === "football" ? (match.kickoff || "00:00") : (match.time || "00:00");
  if (!date) return 0;
  const parsed = new Date(`${date}T${time}`).getTime();
  return isNaN(parsed) ? 0 : parsed;
}

// Helper : determine si match est aujourd'hui / demain / plus tard
function getDayLabel(timestamp) {
  if (!timestamp) return "";
  const today = new Date();
  const matchDate = new Date(timestamp);
  if (isNaN(matchDate.getTime())) return "";

  const todayStr = today.toISOString().slice(0, 10);
  const tomorrowStr = new Date(today.getTime() + 86400000).toISOString().slice(0, 10);
  const matchDateStr = matchDate.toISOString().slice(0, 10);

  if (matchDateStr === todayStr) return "AUJOURD'HUI";
  if (matchDateStr === tomorrowStr) return "DEMAIN";
  return matchDateStr;
}


window.HomePage = function HomePage({ onMatchClick, onTennisMatchClick }) {
  const [footMatches, setFootMatches] = useStateH(null);
  const [tennisMatches, setTennisMatches] = useStateH(null);
  const [loading, setLoading] = useStateH(true);
  const [filterSport, setFilterSport] = useStateH("all");

  useEffectH(() => {
    async function loadAll() {
      // Charger foot
      let foot = [];
      try {
        const apiBase = (window.API_BASE !== undefined ? window.API_BASE : "");
        const ctrl = new AbortController();
        const t = setTimeout(() => ctrl.abort(), 1500);
        const r = await fetch(`${apiBase}/api/matches`, { signal: ctrl.signal });
        clearTimeout(t);
        if (r.ok) foot = await r.json();
      } catch (e) {
        // fallback statique
        try {
          const r = await fetch("./data.json");
          if (r.ok) {
            const d = await r.json();
            foot = d.matches_summary || [];
          }
        } catch (e2) {}
      }

      // Charger tennis
      let tennis = [];
      try {
        const apiBase = (window.API_BASE !== undefined ? window.API_BASE : "");
        const ctrl = new AbortController();
        const t = setTimeout(() => ctrl.abort(), 3000);
        const r = await fetch(`${apiBase}/api/tennis/matches`, { signal: ctrl.signal });
        clearTimeout(t);
        if (r.ok) tennis = await r.json();
      } catch (e) {
        // Fallback 1 : essayer /api/tennis-data (backend renvoie le JSON brut)
        try {
          const apiBase = (window.API_BASE !== undefined ? window.API_BASE : "");
          const r = await fetch(`${apiBase}/api/tennis-data`);
          if (r.ok) {
            const d = await r.json();
            tennis = d.matches || [];
          }
        } catch (e2) {
          // Fallback 2 : fichier statique local (dev)
          try {
            const r = await fetch("./data_tennis.json");
            if (r.ok) {
              const d = await r.json();
              tennis = d.matches || [];
            }
          } catch (e3) {}
        }
      }

      setFootMatches(foot);
      setTennisMatches(tennis);
      setLoading(false);
    }
    loadAll();
  }, []);

  if (loading) return <window.Loading label="Chargement matchs du jour" />;

  // Foot temporairement masque (fin de saison, pas rentable d'acheter plan pro)
  const foot = [];  // footMatches || [];
  const tennis = tennisMatches || [];

  // Construire liste unifiee avec sport et timestamp
  const allMatches = [
    ...foot.map(m => ({ ...m, _sport: "football", _ts: getMatchTimestamp(m, "football") })),
    ...tennis.map(m => ({ ...m, _sport: "tennis", _ts: getMatchTimestamp(m, "tennis") })),
  ];

  // Trier par timestamp croissant (plus proche en haut)
  allMatches.sort((a, b) => {
    if (a._ts < b._ts) return -1;
    if (a._ts > b._ts) return 1;
    return 0;
  });

  // Filtrer par sport
  const filtered = filterSport === "all"
    ? allMatches
    : allMatches.filter(m => m._sport === filterSport);

  // Stats
  const totalValueBets = allMatches.reduce((s, m) => s + (m.value_bets?.length || (m.value_bets_count || 0)), 0);

  // Grouper par jour pour afficher les separateurs
  const grouped = [];
  let currentDay = null;
  for (const m of filtered) {
    const dayLabel = getDayLabel(m._ts);
    if (dayLabel !== currentDay) {
      currentDay = dayLabel;
      grouped.push({ type: "separator", label: dayLabel });
    }
    grouped.push({ type: "match", match: m });
  }

  if (allMatches.length === 0) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-20 text-center fade-in">
        <div className="font-display text-5xl text-[var(--amber)] mb-4">PAS DE MATCHS</div>
        <div className="font-mono text-sm text-[var(--text-muted)] mb-6">
          Lance les jobs pour generer les donnees :
        </div>
        <div className="card p-6 text-left max-w-xl mx-auto">
          <pre className="font-mono text-xs text-[var(--text-secondary)] whitespace-pre-wrap">
{`cd backend
$env:API_FOOTBALL_KEY = "ta_cle"
python -m jobs.refresh_data

$env:RAPIDAPI_KEY = "ta_cle"
python -m jobs.refresh_tennis`}
          </pre>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 fade-in">
      {/* HEADER */}
      <div className="mb-10">
        <div className="font-mono text-[10px] text-[var(--accent)] uppercase tracking-widest">
          MATCHS DU JOUR · TOUS SPORTS
        </div>
        <h1 className="font-display text-6xl mt-1 leading-none">
          {allMatches.length} MATCHS<span className="text-[var(--accent)]">.</span>
        </h1>
        <div className="mt-4 grid grid-cols-4 gap-6 max-w-3xl">
          <div>
            <div className="stat-label">FOOTBALL</div>
            <div className="font-display text-3xl mt-1">{foot.length}</div>
          </div>
          <div>
            <div className="stat-label">TENNIS</div>
            <div className="font-display text-3xl mt-1">{tennis.length}</div>
          </div>
          <div>
            <div className="stat-label">VALUE BETS</div>
            <div className="font-display text-3xl mt-1 text-[var(--accent)]">{totalValueBets}</div>
          </div>
          <div>
            <div className="stat-label">TRI</div>
            <div className="font-mono text-sm mt-1 text-[var(--text-secondary)]">CHRONOLOGIQUE</div>
          </div>
        </div>
      </div>

      {/* FILTRE SPORT */}
      {/* Filtre sport masque (uniquement tennis pour le moment) */}
      {false && (
        <div className="flex items-center gap-3 mb-6">
          <span className="font-mono text-[10px] uppercase tracking-widest text-[var(--text-muted)]">
            FILTRE
          </span>
          {[
            { id: "all", label: "TOUS" },
            { id: "tennis", label: `TENNIS (${tennis.length})` },
          ].map(f => (
            <button
              key={f.id}
              className={`btn ${filterSport === f.id ? "btn-primary" : ""}`}
              onClick={() => setFilterSport(f.id)}
            >
              {f.label}
            </button>
          ))}
        </div>
      )}

      {/* GRILLE DE CARDS UNIFIEE */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {grouped.map((item, i) => {
          if (item.type === "separator") {
            return (
              <div key={`sep-${i}`} className="col-span-full flex items-center gap-3 pt-4 pb-2">
                <div className="font-mono text-[10px] uppercase tracking-widest text-[var(--accent)]">
                  {item.label}
                </div>
                <div className="flex-1 h-px bg-[var(--border)]"></div>
              </div>
            );
          }
          const m = item.match;
          return (
            <div key={`${m._sport}-${m.id}`} style={{ animationDelay: `${i * 30}ms` }} className="fade-in flex justify-center">
              <window.CompactCard
                match={m}
                sport={m._sport}
                onClick={
                  m._sport === "football"
                    ? () => onMatchClick(m.id)
                    : (onTennisMatchClick ? () => onTennisMatchClick(m) : null)
                }
              />
            </div>
          );
        })}
      </div>
    </div>
  );
};
