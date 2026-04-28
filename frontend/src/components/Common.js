// Composants communs
const { useState, useEffect } = React;

// ========== HELPERS ==========
window.helpers = {
  formToLetters(form10) {
    return form10.map(r => r === 1 ? "W" : r === 0 ? "D" : "L");
  },
  pct(v) { return `${v.toFixed(1)}%`; },
  num(v, d = 2) { return v.toFixed(d); },
  formatDate(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString("fr-FR", { day: "2-digit", month: "short" });
  },
  confidenceLabel(score) {
    if (score >= 70) return { label: "ÉLEVÉE", color: "var(--green)" };
    if (score >= 45) return { label: "MOYENNE", color: "var(--amber)" };
    return { label: "FAIBLE", color: "var(--red)" };
  },
};

// ========== HEADER ==========
window.Header = function Header({ active, onNav }) {
  return (
    <header className="header">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <div className="logo">VARION</div>
          <div className="ticker desktop-only">
            <span className="live-dot"></span>
            <span>MODÈLE ACTIF</span>
            <span className="ticker-sep">/</span>
            <span>POISSON × FORME × xG</span>
            <span className="ticker-sep">/</span>
            <span>PREMIER LEAGUE</span>
          </div>
        </div>
        <nav className="flex items-center gap-2">
          {[
            { id: "dashboard", label: "Matchs" },
            { id: "value", label: "Value Bets" },
            { id: "teams", label: "Équipes" },
          ].map(item => (
            <div
              key={item.id}
              className={`nav-link ${active === item.id ? "active" : ""}`}
              onClick={() => onNav(item.id)}
            >
              {item.label}
            </div>
          ))}
        </nav>
      </div>
    </header>
  );
};

// ========== SPINNER ==========
window.Loading = function Loading({ label = "Calcul en cours" }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4">
      <div className="spinner"></div>
      <div className="font-mono text-xs uppercase tracking-widest text-[var(--text-muted)]">
        {label}
      </div>
    </div>
  );
};

// ========== STAT BLOCK ==========
window.StatBlock = function StatBlock({ label, value, suffix = "", trend = null, big = false }) {
  return (
    <div>
      <div className="stat-label">{label}</div>
      <div className="flex items-baseline gap-1 mt-1">
        <span className={`stat-num ${big ? "text-4xl" : "text-2xl"}`}>{value}</span>
        {suffix && <span className="text-xs text-[var(--text-muted)] font-mono">{suffix}</span>}
        {trend !== null && (
          <span className={`text-xs font-mono ml-1 ${trend > 0 ? "text-[var(--green)]" : trend < 0 ? "text-[var(--red)]" : "text-[var(--text-muted)]"}`}>
            {trend > 0 ? "▲" : trend < 0 ? "▼" : "—"}
          </span>
        )}
      </div>
    </div>
  );
};

// ========== PROBA GAUGE 1X2 ==========
window.ProbaGauge = function ProbaGauge({ home, draw, away, homeLabel, awayLabel }) {
  return (
    <div>
      <div className="flex justify-between text-[10px] font-mono uppercase tracking-wider text-[var(--text-muted)] mb-1">
        <span>{homeLabel}</span>
        <span>NUL</span>
        <span>{awayLabel}</span>
      </div>
      <div className="proba-gauge">
        <div className="proba-segment home" style={{ width: `${home}%` }}>
          {home > 12 && `${home.toFixed(0)}%`}
        </div>
        <div className="proba-segment draw" style={{ width: `${draw}%` }}>
          {draw > 12 && `${draw.toFixed(0)}%`}
        </div>
        <div className="proba-segment away" style={{ width: `${away}%` }}>
          {away > 12 && `${away.toFixed(0)}%`}
        </div>
      </div>
    </div>
  );
};

// ========== FORM PILLS ==========
window.FormPills = function FormPills({ form }) {
  const letters = window.helpers.formToLetters(form);
  return (
    <div className="flex">
      {letters.map((l, i) => (
        <div key={i} className={`form-pill form-${l}`} title={`Match ${i + 1}: ${l}`}>{l}</div>
      ))}
    </div>
  );
};

// ========== SCORE METER (0-100) ==========
window.ScoreMeter = function ScoreMeter({ value, label, color = "var(--accent)" }) {
  return (
    <div>
      <div className="flex justify-between items-baseline mb-1">
        <span className="stat-label">{label}</span>
        <span className="font-mono text-sm font-semibold">{value.toFixed(0)}</span>
      </div>
      <div className="progress">
        <div className="progress-fill" style={{ width: `${value}%`, background: color }}></div>
      </div>
    </div>
  );
};

// Cache des SVG charges
window.__LOGO_CACHE = {};
window.__LOGO_FAILED = {};

// ========== TEAM LOGO BLOCK ==========
window.TeamLogo = function TeamLogo({ team, size = 40 }) {
  const [svgContent, setSvgContent] = useState(window.__LOGO_CACHE[team?.id] || null);
  const [failed, setFailed] = useState(window.__LOGO_FAILED[team?.id] || false);

  useEffect(() => {
    if (!team || svgContent || failed) return;
    if (window.__LOGO_CACHE[team.id]) {
      setSvgContent(window.__LOGO_CACHE[team.id]);
      return;
    }
    // Charger le SVG local : ./logos/{TEAM_ID}.svg
    fetch(`./logos/${team.id}.svg`)
      .then(r => {
        if (!r.ok) throw new Error("404");
        return r.text();
      })
      .then(svg => {
        // Sécurité minimum : retirer les scripts éventuels du SVG
        const clean = svg.replace(/<script[\s\S]*?<\/script>/gi, "");
        window.__LOGO_CACHE[team.id] = clean;
        setSvgContent(clean);
      })
      .catch(() => {
        window.__LOGO_FAILED[team.id] = true;
        setFailed(true);
      });
  }, [team?.id]);

  if (!team) return null;

  // SVG officiel chargé : on l'affiche directement
  if (svgContent) {
    return (
      <div
        style={{
          width: size,
          height: size,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        <div
          style={{ width: "100%", height: "100%" }}
          dangerouslySetInnerHTML={{ __html: svgContent }}
        />
      </div>
    );
  }

  // En cours de chargement : skeleton discret
  if (!failed) {
    return (
      <div
        style={{
          width: size,
          height: size,
          background: "var(--bg-elev)",
          border: "1px solid var(--border)",
          flexShrink: 0,
        }}
      />
    );
  }

  // Echec du chargement : carre couleur + abréviation (fallback final)
  return (
    <div
      style={{
        width: size,
        height: size,
        background: team.logo_color || "#444",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "Bebas Neue",
        fontSize: size * 0.45,
        color: "white",
        letterSpacing: "0.05em",
        border: "1px solid var(--border)",
        flexShrink: 0,
      }}
    >
      {team.short ? team.short.substring(0, 3).toUpperCase() : team.id}
    </div>
  );
};

// ========== CONFIDENCE BAR ==========
window.ConfidenceBar = function ConfidenceBar({ score }) {
  const conf = window.helpers.confidenceLabel(score);
  return (
    <div>
      <div className="flex justify-between mb-2">
        <span className="stat-label">Score de confiance</span>
        <span className="font-mono text-sm font-semibold" style={{ color: conf.color }}>
          {score}/100 — {conf.label}
        </span>
      </div>
      <div className="confidence-bar">
        <div className="confidence-fill" style={{ width: "100%" }}></div>
        <div className="confidence-marker" style={{ left: `${score}%` }}></div>
      </div>
    </div>
  );
};
