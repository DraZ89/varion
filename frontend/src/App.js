// VARION - App principal avec routing multi-sport

const { useState: useStateApp, useEffect: useEffectApp } = React;


// ========== FOOTBALL PAGE (matches list, ex-Dashboard) ==========
function FootballPage({ onMatchClick }) {
  const [matches, setMatches] = useStateApp([]);
  const [loading, setLoading] = useStateApp(true);
  const [error, setError] = useStateApp(null);

  useEffectApp(() => {
    window.api.matches()
      .then(d => { setMatches(d || []); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  if (loading) return <window.Loading label="Chargement matchs football" />;
  if (error) return (
    <div className="max-w-3xl mx-auto px-6 py-20 text-center">
      <div className="font-display text-3xl text-[var(--red)] mb-3">CONNEXION IMPOSSIBLE</div>
      <div className="font-mono text-sm text-[var(--text-muted)]">{error}</div>
      <div className="mt-6 font-mono text-xs text-[var(--text-muted)]">
        Lance le backend ou genere data.json avec : python -m jobs.refresh_data
      </div>
    </div>
  );

  if (!matches || matches.length === 0) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-20 text-center fade-in">
        <div className="font-display text-5xl text-[var(--amber)] mb-4">⚽ PAS DE MATCHS FOOT</div>
        <div className="font-mono text-sm text-[var(--text-muted)]">
          Lance : python -m jobs.refresh_data
        </div>
      </div>
    );
  }

  const totalValue = matches.reduce((s, m) => s + (m.value_bets_count || 0), 0);
  const avgGoals = matches.reduce((s, m) => s + (m.predictions_summary?.expected_goals || 0), 0) / Math.max(1, matches.length);

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 fade-in">
      <div className="mb-10">
        <div className="font-mono text-[10px] text-[var(--accent)] uppercase tracking-widest">
          FOOTBALL · MATCHS À VENIR
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
            <div className="stat-label">LIGUES</div>
            <div className="font-mono text-sm mt-1 text-[var(--text-secondary)]">TOP 5 EUROPÉENS</div>
          </div>
        </div>
      </div>

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


// ========== APP ROUTER ==========
function App() {
  const [view, setView] = useStateApp("home");  // home par defaut
  const [selectedMatch, setSelectedMatch] = useStateApp(null);
  const [selectedTennisMatch, setSelectedTennisMatch] = useStateApp(null);
  const [, forceUpdate] = useStateApp({});

  // Re-render global quand la langue change
  useEffectApp(() => {
    const handler = () => forceUpdate({});
    window.addEventListener("varion-lang-change", handler);
    return () => window.removeEventListener("varion-lang-change", handler);
  }, []);

  const handleMatchClick = (id) => {
    setSelectedMatch(id);
    setSelectedTennisMatch(null);
    setView("match");
  };

  // Click sur card tennis : on stocke le match complet
  const handleTennisMatchClick = (tennisMatch) => {
    setSelectedTennisMatch(tennisMatch);
    setSelectedMatch(null);
    setView("tennis-detail");
  };

  const handleBack = () => {
    setSelectedMatch(null);
    setSelectedTennisMatch(null);
    setView("home");
  };

  const handleNav = (id) => {
    setSelectedMatch(null);
    setSelectedTennisMatch(null);
    setView(id);
  };

  let content;
  if (view === "match" && selectedMatch) {
    content = <window.MatchDetail matchId={selectedMatch} onBack={handleBack} />;
  } else if (view === "tennis-detail" && selectedTennisMatch) {
    content = <window.TennisDetail match={selectedTennisMatch} onBack={handleBack} />;
  } else if (view === "football") {
    content = <FootballPage onMatchClick={handleMatchClick} />;
  } else if (view === "tennis") {
    content = <window.TennisPage onMatchClick={handleTennisMatchClick} />;
  } else if (view === "value") {
    content = <window.ValueBetsPage onMatchClick={handleMatchClick} />;
  } else if (view === "ai-stats") {
    content = <window.AiStats />;
  } else {
    // Default = home (multi-sport)
    content = <window.HomePage onMatchClick={handleMatchClick} onTennisMatchClick={handleTennisMatchClick} />;
  }

  // Pour le header actif : si on est sur la page detail, on affiche le sport correspondant
  let activeNav = "home";
  if (view === "football" || view === "match") activeNav = "football";
  else if (view === "tennis" || view === "tennis-detail") activeNav = "tennis";
  else if (view === "value") activeNav = "value";
  else if (view === "home") activeNav = "home";

  return (
    <div>
      <window.Header active={activeNav} onNav={handleNav} />
      {content}
      <footer className="border-t border-[var(--border)] py-8 mt-12">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
          <div className="font-mono text-[10px] text-[var(--text-muted)] uppercase tracking-widest">
            VARION · SPORTS BETTING ANALYTICS · MVP v1.0
          </div>
          <div className="font-mono text-[10px] text-[var(--text-muted)] uppercase tracking-widest">
            POISSON BIVARIÉ × DIXON-COLES × ELO × xG/xA × FORME PONDÉRÉE
          </div>
        </div>
      </footer>
    </div>
  );
}


ReactDOM.createRoot(document.getElementById("root")).render(<App />);
