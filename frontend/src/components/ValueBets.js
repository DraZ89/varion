// Value Bets Page - aggregation across all matches

const { useState: useStateVB, useEffect: useEffectVB } = React;

window.ValueBetsPage = function ValueBetsPage({ onMatchClick }) {
  const [bets, setBets] = useStateVB([]);
  const [minEdge, setMinEdge] = useStateVB(5);
  const [loading, setLoading] = useStateVB(true);

  useEffectVB(() => {
    setLoading(true);
    window.api.valueBets(minEdge)
      .then(d => { setBets(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [minEdge]);

  if (loading) return <window.Loading label="Détection des value bets" />;

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 fade-in">
      <div className="flex items-end justify-between mb-8">
        <div>
          <div className="font-mono text-[10px] text-[var(--accent)] uppercase tracking-widest">
            VALUE BET ENGINE
          </div>
          <h1 className="font-display text-5xl mt-1">OPPORTUNITÉS</h1>
          <div className="font-mono text-xs text-[var(--text-muted)] uppercase tracking-widest mt-2">
            COTES BOOKMAKER VS PROBABILITÉS MODÈLE · {bets.length} OPPORTUNITÉS DÉTECTÉES
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

      {bets.length === 0 ? (
        <div className="card p-12 text-center">
          <div className="font-display text-3xl text-[var(--text-muted)] mb-2">PAS DE VALUE</div>
          <div className="font-mono text-sm text-[var(--text-muted)]">
            Aucun pari ne dépasse le seuil d'edge configuré.
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {bets.map((bet, i) => (
            <div
              key={i}
              className="card card-hover p-5 cursor-pointer"
              onClick={() => onMatchClick(bet.match_id)}
            >
              <div className="grid grid-cols-12 gap-4 items-center">
                <div className="col-span-3">
                  <div className="font-mono text-[10px] text-[var(--text-muted)] uppercase tracking-widest">
                    {bet.match_date} · {bet.match_kickoff}
                  </div>
                  <div className="font-display text-xl mt-1">{bet.match_label}</div>
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
          ))}
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
