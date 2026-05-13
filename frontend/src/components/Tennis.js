// Composants tennis - liste de matchs du jour

const { useState: useStateT, useEffect: useEffectT } = React;

// ========== TENNIS PAGE ==========

window.TennisPage = function TennisPage({ onMatchClick }) {
  const [matches, setMatches] = useStateT(null);
  const [loading, setLoading] = useStateT(true);
  const [filterTour, setFilterTour] = useStateT("all");
  const [error, setError] = useStateT(null);

  useEffectT(() => {
    setLoading(true);

    const tryFetch = async () => {
      // Essai backend
      try {
        const apiBase = (window.API_BASE !== undefined ? window.API_BASE : "");
        const ctrl = new AbortController();
        const t = setTimeout(() => ctrl.abort(), 3000);
        const live = await fetch(`${apiBase}/api/tennis/matches`, { signal: ctrl.signal });
        clearTimeout(t);
        if (live.ok) return live.json();
      } catch (e) {}

      // Fallback 1 : /api/tennis-data
      try {
        const apiBase = (window.API_BASE !== undefined ? window.API_BASE : "");
        const r = await fetch(`${apiBase}/api/tennis-data`);
        if (r.ok) {
          const data = await r.json();
          return data.matches || [];
        }
      } catch (e) {}

      // Fallback 2 : statique local (dev)
      try {
        const res = await fetch("./data_tennis.json");
        if (res.ok) {
          const data = await res.json();
          return data.matches || [];
        }
      } catch (e) {}
      return null;
    };

    tryFetch()
      .then(data => {
        if (!data) {
          setError("Donnees tennis non generees. Lance : python -m jobs.refresh_tennis");
        } else {
          setMatches(data);
        }
        setLoading(false);
      });
  }, []);

  if (loading) return <window.Loading label="Chargement matchs tennis" />;

  if (error || !matches) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-20 text-center fade-in">
        <div className="font-display text-4xl text-[var(--amber)] mb-4">🎾 PAS ENCORE DE DONNEES TENNIS</div>
        <div className="font-mono text-sm text-[var(--text-muted)] mb-6">
          {error || "data_tennis.json est vide"}
        </div>
        <div className="card p-6 text-left">
          <div className="stat-label mb-3">POUR GENERER LES DONNEES</div>
          <pre className="font-mono text-xs text-[var(--text-secondary)] whitespace-pre-wrap">
{`cd backend
$env:RAPIDAPI_KEY = "ta_cle"
python -m jobs.refresh_tennis`}
          </pre>
        </div>
      </div>
    );
  }

  const filtered = filterTour === "all"
    ? matches
    : matches.filter(m => m.tour && m.tour.toLowerCase() === filterTour);

  const atpCount = matches.filter(m => m.tour === "ATP").length;
  const wtaCount = matches.filter(m => m.tour === "WTA").length;
  const totalValueBets = matches.reduce((s, m) => s + (m.value_bets?.length || 0), 0);

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 fade-in">
      <div className="mb-10">
        <div className="font-mono text-[10px] text-[var(--accent)] uppercase tracking-widest">
          TENNIS · MATCHS DU JOUR
        </div>
        <h1 className="font-display text-6xl mt-1 leading-none">
          {matches.length} MATCHS<span className="text-[var(--accent)]">.</span>
        </h1>
        <div className="mt-4 grid grid-cols-4 gap-6 max-w-3xl">
          <div>
            <div className="stat-label">ATP</div>
            <div className="font-display text-3xl mt-1">{atpCount}</div>
          </div>
          <div>
            <div className="stat-label">WTA</div>
            <div className="font-display text-3xl mt-1">{wtaCount}</div>
          </div>
          <div>
            <div className="stat-label">VALUE BETS</div>
            <div className="font-display text-3xl mt-1 text-[var(--accent)]">{totalValueBets}</div>
          </div>
          <div>
            <div className="stat-label">MOTEUR</div>
            <div className="font-mono text-sm mt-1 text-[var(--text-secondary)]">ELO + SURFACE</div>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3 mb-6">
        <span className="font-mono text-[10px] uppercase tracking-widest text-[var(--text-muted)]">
          FILTRE
        </span>
        {[
          { id: "all", label: "TOUS" },
          { id: "atp", label: `ATP (${atpCount})` },
          { id: "wta", label: `WTA (${wtaCount})` },
        ].map(f => (
          <button
            key={f.id}
            className={`btn ${filterTour === f.id ? "btn-primary" : ""}`}
            onClick={() => setFilterTour(f.id)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div className="card p-12 text-center">
          <div className="font-display text-3xl text-[var(--text-muted)]">PAS DE MATCH</div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((m, i) => (
            <div key={m.id} style={{ animationDelay: `${i * 50}ms` }} className="fade-in flex justify-center">
              <window.CompactCard
                match={m}
                sport="tennis"
                onClick={onMatchClick ? () => onMatchClick(m) : null}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};


// ========== TENNIS CARD ==========

window.TennisCard = function TennisCard({ match }) {
  const [expanded, setExpanded] = useStateT(false);
  const winner = match.predictions?.winner || {};
  const sets = match.predictions?.sets_score || {};
  const games = match.predictions?.total_games || {};
  const conf = window.helpers.confidenceLabel(match.confidence_score || 0);

  return (
    <div className="card card-hover match-card p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`tag ${match.tour === "ATP" ? "tag-blue" : "tag-amber"}`}>
            {match.tour}
          </span>
          <span className="font-mono text-[10px] uppercase tracking-widest text-[var(--text-muted)]">
            {match.tournament}
          </span>
          {match.round && (
            <span className="font-mono text-[10px] uppercase tracking-widest text-[var(--text-muted)]">
              · {match.round}
            </span>
          )}
          <span className="tag">{match.surface?.toUpperCase()}</span>
          <span className="tag">{match.format}</span>
        </div>
        <span className="font-mono text-xs text-[var(--text-muted)]">
          {match.date} · {match.time}
        </span>
      </div>

      <div className="grid grid-cols-12 gap-4 items-center mb-4">
        <div className="col-span-4">
          <div className="font-display text-xl">{match.player_a.name}</div>
          <div className="font-mono text-[10px] text-[var(--text-muted)] mt-1">
            #{match.player_a.rank || "?"} · ELO {Math.round(winner.elo_a || 0)}
          </div>
        </div>

        <div className="col-span-4 text-center">
          <div className="font-mono text-[10px] uppercase tracking-widest text-[var(--text-muted)] mb-1">VS</div>
          {sets.most_likely && (
            <div className="font-display text-2xl text-[var(--accent)]">
              {sets.most_likely}
            </div>
          )}
        </div>

        <div className="col-span-4 text-right">
          <div className="font-display text-xl">{match.player_b.name}</div>
          <div className="font-mono text-[10px] text-[var(--text-muted)] mt-1">
            ELO {Math.round(winner.elo_b || 0)} · #{match.player_b.rank || "?"}
          </div>
        </div>
      </div>

      <div className="proba-gauge mb-4">
        <div className="proba-segment home" style={{ width: `${winner.prob_a || 50}%`, background: "#2563eb" }}>
          {(winner.prob_a || 0) > 12 && `${(winner.prob_a || 0).toFixed(0)}%`}
        </div>
        <div className="proba-segment away" style={{ width: `${winner.prob_b || 50}%`, background: "#dc2626" }}>
          {(winner.prob_b || 0) > 12 && `${(winner.prob_b || 0).toFixed(0)}%`}
        </div>
      </div>

      <div className="grid grid-cols-4 gap-3 pt-4 border-t border-[var(--border)]">
        <div>
          <div className="stat-label">Total games att.</div>
          <div className="font-mono text-base font-semibold mt-1">
            {(games.expected_total || 0).toFixed(1)}
          </div>
        </div>
        <div>
          <div className="stat-label">H2H</div>
          <div className="font-mono text-base font-semibold mt-1">
            {match.h2h?.wins_a || 0}-{match.h2h?.wins_b || 0}
          </div>
        </div>
        <div>
          <div className="stat-label">Value bets</div>
          <div className="font-mono text-base font-semibold mt-1 text-[var(--accent)]">
            {match.value_bets?.length || 0}
          </div>
        </div>
        <div>
          <div className="stat-label">Confiance</div>
          <div className="font-mono text-base font-semibold mt-1" style={{ color: conf.color }}>
            {match.confidence_score || 0}/100
          </div>
        </div>
      </div>

      {match.value_bets && match.value_bets.length > 0 && (
        <div className="mt-4 pt-4 border-t border-[var(--border)] flex items-center gap-3">
          <span className="tag tag-accent">VALUE BET</span>
          <span className="font-mono text-xs text-[var(--text-secondary)]">
            <span className="text-[var(--accent)] font-semibold">{match.value_bets[0].market}</span>
            {" "}@ <span className="text-white">{match.value_bets[0].odds.toFixed(2)}</span>
            {" "}<span className="text-[var(--green)]">+{match.value_bets[0].edge_pct.toFixed(1)}%</span>
          </span>
        </div>
      )}

      <button
        className="mt-4 pt-4 border-t border-[var(--border)] w-full font-mono text-[10px] uppercase tracking-widest text-[var(--text-muted)] hover:text-[var(--accent)]"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? "− MASQUER L'ANALYSE" : "+ ANALYSE COMPLETE"}
      </button>

      {expanded && (
        <div className="mt-4 pt-4 border-t border-[var(--border)] space-y-4">
          {match.summary && (
            <div>
              <div className="stat-label mb-2">SYNTHESE</div>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{match.summary}</p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="stat-label mb-2">{match.player_a.name} ELO</div>
              <div className="space-y-1 font-mono text-xs">
                {["global", "hard", "clay", "grass"].map(s => (
                  <div key={s} className="flex justify-between">
                    <span className="text-[var(--text-muted)]">{s}</span>
                    <span>{Math.round(match.player_a.elo?.[s] || 0)}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <div className="stat-label mb-2">{match.player_b.name} ELO</div>
              <div className="space-y-1 font-mono text-xs">
                {["global", "hard", "clay", "grass"].map(s => (
                  <div key={s} className="flex justify-between">
                    <span className="text-[var(--text-muted)]">{s}</span>
                    <span>{Math.round(match.player_b.elo?.[s] || 0)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {match.value_bets && match.value_bets.length > 0 && (
            <div>
              <div className="stat-label mb-2">TOUS LES VALUE BETS</div>
              <div className="space-y-2">
                {match.value_bets.map((b, i) => (
                  <div key={i} className="flex items-center justify-between bg-[var(--bg-elev)] p-2 border border-[var(--border)]">
                    <span className="text-sm">{b.market}</span>
                    <div className="flex items-center gap-3 font-mono text-xs">
                      <span>@ {b.odds.toFixed(2)}</span>
                      <span className="text-[var(--accent)]">+{b.edge_pct.toFixed(1)}%</span>
                      <span className={`tag ${b.confidence === "strong" ? "tag-accent" : b.confidence === "high" ? "tag-green" : "tag-amber"}`}>
                        {b.confidence.toUpperCase()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
