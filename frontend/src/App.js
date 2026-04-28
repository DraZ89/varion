// EDGE - App principal

const { useState: useStateApp, useEffect: useEffectApp } = React;

function Dashboard({ onMatchClick }) {
  const [matches, setMatches] = useStateApp([]);
  const [loading, setLoading] = useStateApp(true);
  const [error, setError] = useStateApp(null);

  useEffectApp(() => {
    window.api.matches()
      .then(d => { setMatches(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  if (loading) return <window.Loading label="Chargement des matchs" />;
  if (error) return (
    <div className="max-w-3xl mx-auto px-6 py-20 text-center">
      <div className="font-display text-3xl text-[var(--red)] mb-3">CONNEXION IMPOSSIBLE</div>
      <div className="font-mono text-sm text-[var(--text-muted)]">{error}</div>
      <div className="mt-6 font-mono text-xs text-[var(--text-muted)]">
        Assurez-vous que le backend tourne sur http://localhost:8000
      </div>
    </div>
  );

  // Stats agrégées
  const totalValue = matches.reduce((s, m) => s + m.value_bets_count, 0);
  const avgGoals = matches.reduce((s, m) => s + m.predictions_summary.expected_goals, 0) / Math.max(1, matches.length);

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 fade-in">
      {/* HERO */}
      <div className="mb-10">
        <div className="font-mono text-[10px] text-[var(--accent)] uppercase tracking-widest">
          DASHBOARD · MATCHS À VENIR
        </div>
        <h1 className="font-display text-6xl mt-1 leading-none">
          {matches.length} MATCHS<span className="text-[var(--accent)]">.</span>
        </h1>
        <div className="mt-4 grid grid-cols-4 gap-6 max-w-3xl">
          <div>
            <div className="stat-label">VALUE BETS DÉTECTÉS</div>
            <div className="font-display text-3xl mt-1 text-[var(--accent)]">{totalValue}</div>
          </div>
          <div>
            <div className="stat-label">BUTS MOYENS PRÉVUS</div>
            <div className="font-display text-3xl mt-1">{avgGoals.toFixed(2)}</div>
          </div>
          <div>
            <div className="stat-label">MOTEUR</div>
            <div className="font-mono text-sm mt-1 text-[var(--text-secondary)]">POISSON × xG</div>
          </div>
          <div>
            <div className="stat-label">DERNIÈRE MAJ</div>
            <div className="font-mono text-sm mt-1 text-[var(--text-secondary)]">À L'INSTANT</div>
          </div>
        </div>
      </div>

      {/* MATCHES LIST */}
      <div className="space-y-4">
        {matches.map((m, i) => (
          <div key={m.id} style={{ animationDelay: `${i * 60}ms` }} className="fade-in">
            <window.MatchCard match={m} onClick={() => onMatchClick(m.id)} />
          </div>
        ))}
      </div>
    </div>
  );
}


function App() {
  const [view, setView] = useStateApp("dashboard");
  const [selectedMatch, setSelectedMatch] = useStateApp(null);

  const handleMatchClick = (id) => {
    setSelectedMatch(id);
    setView("match");
  };

  const handleBack = () => {
    setSelectedMatch(null);
    setView("dashboard");
  };

  const handleNav = (id) => {
    setSelectedMatch(null);
    setView(id);
  };

  let content;
  if (view === "match" && selectedMatch) {
    content = <window.MatchDetail matchId={selectedMatch} onBack={handleBack} />;
  } else if (view === "value") {
    content = <window.ValueBetsPage onMatchClick={handleMatchClick} />;
  } else if (view === "teams") {
    content = <window.TeamsPage />;
  } else {
    content = <Dashboard onMatchClick={handleMatchClick} />;
  }

  return (
    <div>
      <window.Header active={view === "match" ? "dashboard" : view} onNav={handleNav} />
      {content}
      <footer className="border-t border-[var(--border)] py-8 mt-12">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
          <div className="font-mono text-[10px] text-[var(--text-muted)] uppercase tracking-widest">
            VARION · SPORTS BETTING ANALYTICS · MVP v1.0
          </div>
          <div className="font-mono text-[10px] text-[var(--text-muted)] uppercase tracking-widest">
            POISSON BIVARIÉ × DIXON-COLES × xG/xA × FORME PONDÉRÉE
          </div>
        </div>
      </footer>
    </div>
  );
}


ReactDOM.createRoot(document.getElementById("root")).render(<App />);
