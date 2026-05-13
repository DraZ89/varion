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
  const [, forceUpdate] = React.useState({});
  const [langOpen, setLangOpen] = React.useState(false);

  // Re-render quand la langue ou le theme changent
  React.useEffect(() => {
    const handler = () => forceUpdate({});
    window.addEventListener("varion-lang-change", handler);
    return () => window.removeEventListener("varion-lang-change", handler);
  }, []);

  const t = window.t || ((k, f) => f || k);
  const currentLang = window.__VARION_LANG || "fr";
  const currentTheme = window.__VARION_THEME || "dark";

  const langs = [
    { code: "fr", label: "Français", flag: "FR" },
    { code: "en", label: "English", flag: "GB" },
    { code: "es", label: "Español", flag: "ES" },
  ];
  const currentLangObj = langs.find(l => l.code === currentLang) || langs[0];

  const toggleTheme = () => {
    window.setTheme(currentTheme === "dark" ? "light" : "dark");
    forceUpdate({});
  };

  const handleSelectLang = (lang) => {
    window.setLang(lang);
    setLangOpen(false);
  };

  // Close dropdown on outside click
  React.useEffect(() => {
    if (!langOpen) return;
    const handler = (e) => {
      if (!e.target.closest(".lang-selector")) setLangOpen(false);
    };
    document.addEventListener("click", handler);
    return () => document.removeEventListener("click", handler);
  }, [langOpen]);

  return (
    <header className="varion-header">
      <div className="varion-header-inner">
        {/* Wordmark */}
        <div className="varion-wordmark" onClick={() => onNav("home")} style={{ cursor: "pointer" }}>
          <div className="varion-symbol">
            <div className="varion-symbol-inner"></div>
          </div>
          <span className="varion-name">Varion</span>
          <span className="varion-subtitle">{t("app.subtitle", "Sports betting analytics")}</span>
        </div>

        {/* Nav */}
        <nav className="varion-nav">
          {[
            { id: "home", label: t("nav.home", "Accueil") },
            // Foot temporairement masque (fin de saison, pas rentable d'acheter plan pro)
            // { id: "football", label: t("nav.football", "Foot") },
            { id: "tennis", label: t("nav.tennis", "Tennis") },
            { id: "value", label: t("nav.value", "Value Bets") },
            { id: "ai-stats", label: t("nav.aiStats", "Performance IA") },
          ].map(item => (
            <button
              key={item.id}
              className={`varion-nav-link ${active === item.id ? "active" : ""}`}
              onClick={() => onNav(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>

        {/* Controls : theme toggle + lang selector */}
        <div className="header-controls">
          {/* Theme toggle */}
          <button
            className="icon-btn"
            onClick={toggleTheme}
            title={currentTheme === "dark" ? "Mode clair" : "Mode sombre"}
            aria-label="Toggle theme"
          >
            {currentTheme === "dark" ? (
              // Soleil (passer en clair)
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="4" />
                <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
              </svg>
            ) : (
              // Lune (passer en sombre)
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
            )}
          </button>

          {/* Lang selector */}
          <div className="lang-selector">
            <button
              className="lang-selector-btn"
              onClick={(e) => { e.stopPropagation(); setLangOpen(!langOpen); }}
            >
              <span className="lang-selector-current">
                <window.Flag country={currentLangObj.flag} width={20} height={14}/>
                <span style={{ textTransform: "uppercase", fontWeight: 600, fontSize: 12 }}>{currentLangObj.code}</span>
              </span>
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="6 9 12 15 18 9"/></svg>
            </button>
            {langOpen && (
              <div className="lang-dropdown">
                {langs.map(l => (
                  <div
                    key={l.code}
                    className={`lang-option ${currentLang === l.code ? "active" : ""}`}
                    onClick={() => handleSelectLang(l.code)}
                  >
                    <window.Flag country={l.flag} width={22} height={16}/>
                    <span>{l.label}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
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

// Cache des SVG charges (data URIs)
window.__LOGO_CACHE = {};
window.__LOGO_FAILED = {};

// Convertit un SVG (string) en data URI utilisable dans <img src>
function svgToDataUri(svgString) {
  // Encoder pour gérer les caractères spéciaux (UTF-8)
  const encoded = encodeURIComponent(svgString)
    .replace(/'/g, "%27")
    .replace(/"/g, "%22");
  return `data:image/svg+xml;charset=utf-8,${encoded}`;
}

// Vérifie que le contenu est bien un SVG (et pas un PNG ou autre)
function isValidSvg(content) {
  if (!content || typeof content !== "string") return false;
  const trimmed = content.trim().toLowerCase();
  // Doit commencer par <?xml ou <svg
  if (!(trimmed.startsWith("<?xml") || trimmed.startsWith("<svg"))) return false;
  // Doit contenir une balise svg
  return /<svg[\s>]/i.test(content);
}

// ========== TEAM LOGO BLOCK ==========
window.TeamLogo = function TeamLogo({ team, size = 40 }) {
  const [dataUri, setDataUri] = useState(window.__LOGO_CACHE[team?.id] || null);
  const [failed, setFailed] = useState(window.__LOGO_FAILED[team?.id] || false);

  useEffect(() => {
    if (!team || dataUri || failed) return;
    if (window.__LOGO_CACHE[team.id]) {
      setDataUri(window.__LOGO_CACHE[team.id]);
      return;
    }
    fetch(`./logos/${team.id}.svg`)
      .then(r => {
        if (!r.ok) throw new Error("404");
        return r.text();
      })
      .then(svg => {
        // Vérifier que c'est bien un SVG (pas un PNG renommé en .svg)
        if (!isValidSvg(svg)) {
          throw new Error("not a valid SVG file");
        }
        // Sécurité : retirer les scripts éventuels
        const clean = svg.replace(/<script[\s\S]*?<\/script>/gi, "");
        const uri = svgToDataUri(clean);
        window.__LOGO_CACHE[team.id] = uri;
        setDataUri(uri);
      })
      .catch(() => {
        window.__LOGO_FAILED[team.id] = true;
        setFailed(true);
      });
  }, [team?.id]);

  if (!team) return null;

  // SVG officiel chargé : on l'affiche dans une <img> (qui contraint la taille)
  if (dataUri) {
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
        <img
          src={dataUri}
          alt={team.short || team.name}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "contain",
            display: "block",
          }}
          onError={() => {
            window.__LOGO_FAILED[team.id] = true;
            setFailed(true);
            setDataUri(null);
          }}
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
        fontFamily: "Sora, sans-serif",
        fontSize: size * 0.45,
        fontWeight: 700,
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
