// Value Bets Page - aggregation across all matches

const { useState: useStateVB, useEffect: useEffectVB } = React;

window.ValueBetsPage = function ValueBetsPage({ onMatchClick }) {
  const [bets, setBets] = useStateVB([]);
  const [minEdge, setMinEdge] = useStateVB(5);
  const [loading, setLoading] = useStateVB(true);
  const [filterSport, setFilterSport] = useStateVB("all");

  useEffectVB(() => {
    setLoading(true);
    async function loadAll() {
      // Foot
      let footBets = [];
      try {
        footBets = await window.api.valueBets(minEdge) || [];
        footBets = footBets.map(b => ({ ...b, _sport: "football" }));
      } catch (e) {
        // fallback statique
        try {
          const r = await fetch("./data.json");
          if (r.ok) {
            const d = await r.json();
            footBets = (d.value_bets || [])
              .filter(b => b.edge_pct >= minEdge)
              .map(b => ({ ...b, _sport: "football" }));
          }
        } catch (e2) {}
      }

      // Tennis
      let tennisBets = [];
      try {
        const apiBase = (window.API_BASE !== undefined ? window.API_BASE : "");
        const ctrl = new AbortController();
        const t = setTimeout(() => ctrl.abort(), 3000);
        const r = await fetch(`${apiBase}/api/tennis/value-bets?min_edge=${minEdge}`, { signal: ctrl.signal });
        clearTimeout(t);
        if (r.ok) {
          tennisBets = await r.json();
          tennisBets = tennisBets.map(b => ({ ...b, _sport: "tennis" }));
        }
      } catch (e) {
        // Fallback 1 : /api/tennis-data
        try {
          const apiBase = (window.API_BASE !== undefined ? window.API_BASE : "");
          const r = await fetch(`${apiBase}/api/tennis-data`);
          if (r.ok) {
            const d = await r.json();
            tennisBets = (d.value_bets || [])
              .filter(b => b.edge_pct >= minEdge)
              .map(b => ({ ...b, _sport: "tennis" }));
          }
        } catch (e2) {
          // Fallback 2 : statique
          try {
            const r = await fetch("./data_tennis.json");
            if (r.ok) {
              const d = await r.json();
              tennisBets = (d.value_bets || [])
                .filter(b => b.edge_pct >= minEdge)
                .map(b => ({ ...b, _sport: "tennis" }));
            }
          } catch (e3) {}
        }
      }

      // Merge et tri par edge decroissant
      const allBets = [...footBets, ...tennisBets].sort((a, b) => b.edge_pct - a.edge_pct);
      setBets(allBets);
      setLoading(false);
    }
    loadAll();
  }, [minEdge]);

  if (loading) return <window.Loading label="Détection des value bets" />;

  const filtered = filterSport === "all" ? bets : bets.filter(b => b._sport === filterSport);
  const footCount = bets.filter(b => b._sport === "football").length;
  const tennisCount = bets.filter(b => b._sport === "tennis").length;

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 fade-in">
      <div className="flex items-end justify-between mb-8">
        <div>
          <div className="font-mono text-[10px] text-[var(--accent)] uppercase tracking-widest">
            VALUE BET ENGINE
          </div>
          <h1 className="font-display text-5xl mt-1">OPPORTUNITÉS</h1>
          <div className="font-mono text-xs text-[var(--text-muted)] uppercase tracking-widest mt-2">
            COTES BOOKMAKER VS PROBABILITÉS MODÈLE · {filtered.length} OPPORTUNITÉS DÉTECTÉES
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="font-mono text-[10px] uppercase tracking-widest text-[var(--text-muted)]">
            EDGE MIN.
          </span>
          {[3, 5, 8, 12].map(v => (
            <button
              key={v}
              className={`btn ${minEdge === v ? "btn-primary" : ""}`}
              onClick={() => setMinEdge(v)}
            >
              ≥ {v}%
            </button>
          ))}
        </div>
      </div>

      {/* FILTRE SPORT */}
      <div className="flex items-center gap-3 mb-6">
        <span className="font-mono text-[10px] uppercase tracking-widest text-[var(--text-muted)]">
          SPORT
        </span>
        {[
          { id: "all", label: `TOUS (${bets.length})` },
          { id: "football", label: `FOOT (${footCount})` },
          { id: "tennis", label: `TENNIS (${tennisCount})` },
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

      {filtered.length === 0 ? (
        <div className="card p-12 text-center">
          <div className="font-display text-3xl text-[var(--text-muted)] mb-2">PAS DE VALUE</div>
          <div className="font-mono text-sm text-[var(--text-muted)]">
            Aucun pari ne dépasse le seuil d'edge configuré.
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((bet, i) => {
            const isTennis = bet._sport === "tennis";
            const dateStr = bet.match_date || bet.date || "";
            const timeStr = bet.match_kickoff || bet.time || "";
            const handleClick = isTennis
              ? null  // Tennis : pas de page de detail pour l'instant
              : () => onMatchClick(bet.match_id);

            return (
            <div
              key={i}
              className={`card ${isTennis ? "" : "card-hover cursor-pointer"} p-5`}
              onClick={handleClick}
            >
              <div className="grid grid-cols-12 gap-4 items-center">
                <div className="col-span-3">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`tag ${isTennis ? (bet.tour === "WTA" ? "tag-amber" : "tag-blue") : "tag-blue"}`}>
                      {isTennis ? bet.tour : "FOOT"}
                    </span>
                    <div className="font-mono text-[10px] text-[var(--text-muted)] uppercase tracking-widest">
                      {dateStr}{timeStr ? ` · ${timeStr}` : ""}
                    </div>
                  </div>
                  <div className="font-display text-xl mt-1">{bet.match_label}</div>
                  {bet.tournament && (
                    <div className="font-mono text-[10px] text-[var(--text-muted)] mt-1">
                      {bet.tournament}
                    </div>
                  )}
                </div>

                <div className="col-span-4">
                  <div className="stat-label">MARCHÉ</div>
                  <div className="font-medium mt-1">{bet.market}</div>
                  <div className="font-mono text-xs text-[var(--text-muted)] mt-1">
                    Sélection : <span className="text-[var(--text-primary)]">{bet.selection}</span>
                  </div>
                </div>

                <div className="col-span-2 text-center">
                  <div className="stat-label">COTE</div>
                  <div className="font-display text-2xl mt-1">{bet.odds.toFixed(2)}</div>
                </div>

                <div className="col-span-2 text-center">
                  <div className="stat-label">PROBAS</div>
                  <div className="font-mono text-sm mt-1">
                    <span className="text-[var(--green)] font-semibold">{bet.model_prob.toFixed(0)}%</span>
                    <span className="text-[var(--text-muted)] mx-1">vs</span>
                    <span className="text-[var(--text-muted)]">{bet.implied_prob.toFixed(0)}%</span>
                  </div>
                </div>

                <div className="col-span-1 text-right">
                  <div className="stat-label">EDGE</div>
                  <div className="font-display text-2xl mt-1 text-[var(--accent)]">
                    +{bet.edge_pct.toFixed(0)}%
                  </div>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-[var(--border)] flex items-center gap-3">
                <span className={`tag ${
                  bet.confidence === "strong" ? "tag-accent" :
                  bet.confidence === "high" ? "tag-green" : "tag-amber"
                }`}>
                  {bet.confidence === "strong" ? "🔥 STRONG" :
                   bet.confidence === "high" ? "✅ HIGH" : "💡 MODERATE"}
                </span>
                <span className="text-xs text-[var(--text-secondary)]">{bet.explanation}</span>
              </div>
            </div>
          );
          })}
        </div>
      )}
    </div>
  );
};


// =============== TEAMS PAGE ===============

window.TeamsPage = function TeamsPage({ onTeamClick }) {
  const [teams, setTeams] = useStateVB([]);
  const [loading, setLoading] = useStateVB(true);

  useEffectVB(() => {
    window.api.teams()
      .then(d => { setTeams(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <window.Loading />;

  const sorted = [...teams].sort((a, b) => a.rank - b.rank);

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 fade-in">
      <div className="mb-8">
        <div className="font-mono text-[10px] text-[var(--accent)] uppercase tracking-widest">
          PREMIER LEAGUE 2025/26
        </div>
        <h1 className="font-display text-5xl mt-1">CLASSEMENT</h1>
      </div>

      <div className="card overflow-hidden">
        <table className="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>ÉQUIPE</th>
              <th className="text-right">PTS</th>
              <th className="text-right">MJ</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {sorted.map(t => (
              <tr key={t.id} className="cursor-pointer" onClick={() => onTeamClick && onTeamClick(t.id)}>
                <td className="font-mono">{t.rank}</td>
                <td>
                  <div className="flex items-center gap-3">
                    <window.TeamLogo team={t} size={28} />
                    <span className="font-medium">{t.name}</span>
                  </div>
                </td>
                <td className="text-right font-semibold">{t.points}</td>
                <td className="text-right text-[var(--text-muted)]">30</td>
                <td className="text-right text-[var(--text-muted)]">→</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
