// ========== AI STATS PAGE ==========
// Page Performance IA : stats de fiabilite des paris IA Varion
// + CTA pour souscrire a Varion Pro
// + Import xlsx pour merger les paris saisis manuellement (suivi_varion.xlsx)

const { useState: useStateAI, useEffect: useEffectAI, useRef: useRefAI } = React;


// Charge la lib SheetJS depuis CDN au premier usage (lazy)
let _xlsxLib = null;
function loadSheetJS() {
  if (_xlsxLib) return Promise.resolve(_xlsxLib);
  if (window.XLSX) {
    _xlsxLib = window.XLSX;
    return Promise.resolve(_xlsxLib);
  }
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js";
    script.onload = () => {
      _xlsxLib = window.XLSX;
      resolve(_xlsxLib);
    };
    script.onerror = reject;
    document.head.appendChild(script);
  });
}


// Parse un xlsx au format "suivi_varion" et retourne les rows {match, type, status, ...}
async function parseSuiviVarionXlsx(file) {
  const XLSX = await loadSheetJS();
  const buf = await file.arrayBuffer();
  const wb = XLSX.read(buf, { cellDates: true });

  // Cherche la feuille "Raw Data" (ou prend la 1ere)
  const sheetName = wb.SheetNames.includes("Raw Data") ? "Raw Data" : wb.SheetNames[0];
  const ws = wb.Sheets[sheetName];
  const rows = XLSX.utils.sheet_to_json(ws, { defval: "" });

  // Normaliser les rows : on extrait les champs interessants
  const normalized = rows.map(r => ({
    date: r["Date"] || r["date"] || "",
    match: r["Match"] || r["match"] || "",
    tournament: r["Tournoi"] || r["Tournament"] || "",
    player_a: r["Joueur1"] || r["Player1"] || "",
    player_b: r["Joueur2"] || r["Player2"] || "",
    predicted_winner: r["Prédit Vainqueur"] || r["Predicted Winner"] || "",
    real_winner: r["Vainqueur Réel"] || r["Real Winner"] || "",
    predicted_score: r["Score prédit"] || r["Predicted Score"] || "",
    real_score: r["Score réel"] || r["Real Score"] || "",
    predicted_games: r["Jeux prédits"] || r["Predicted Games"] || "",
    real_games: r["Jeux réels"] || r["Real Games"] || "",
    type: r["Type"] || "",                          // Principale / Recommandée
    bet_label: r["Pari reco"] || r["Bet"] || "",   // pour les recommandées
    odds: r["Cote"] || r["Cote "] || r["Odds"] || "",
    bet_result: r["Résultat pari"] || r["Bet Result"] || "", // Gagné / Perdu (recommandées)
    surface: r["Surface"] || "",
    tier: r["Niveau Tournoi"] || r["Tier"] || "",
    winner_ok: r["Vainqueur_OK"] || "",
    score_ok: r["Score_OK"] || "",
    games_ok: r["Jeux_OK"] || "",
  })).filter(r => r.match);  // ignore lignes vides

  return normalized;
}


// Calcule les stats globales depuis les rows importes
function computeStatsFromRows(rows) {
  const principales = rows.filter(r => (r.type || "").toLowerCase().includes("principale"));
  const recommandees = rows.filter(r => (r.type || "").toLowerCase().includes("recommand"));

  const countWon = (arr, field) => arr.filter(r => (r[field] || "").toLowerCase() === "gagné").length;
  const countSettled = (arr, field) => arr.filter(r => {
    const v = (r[field] || "").toLowerCase();
    return v === "gagné" || v === "perdu";
  }).length;

  // KPIs principales
  const p_total = principales.length;
  const p_winner_settled = countSettled(principales, "winner_ok");
  const p_winner_won = countWon(principales, "winner_ok");
  const p_winner_rate = p_winner_settled > 0 ? (p_winner_won / p_winner_settled * 100) : 0;

  const p_score_settled = countSettled(principales, "score_ok");
  const p_score_won = countWon(principales, "score_ok");
  const p_score_rate = p_score_settled > 0 ? (p_score_won / p_score_settled * 100) : 0;

  const p_games_settled = countSettled(principales, "games_ok");
  const p_games_won = countWon(principales, "games_ok");
  const p_games_rate = p_games_settled > 0 ? (p_games_won / p_games_settled * 100) : 0;

  // KPIs recommandees
  const r_total = recommandees.length;
  const r_settled = countSettled(recommandees, "bet_result");
  const r_won = countWon(recommandees, "bet_result");
  const r_rate = r_settled > 0 ? (r_won / r_settled * 100) : 0;

  // ROI recommandees : somme (odds - 1) pour gagnees - 1 pour perdues / total
  let profit_units = 0;
  recommandees.forEach(r => {
    const v = (r.bet_result || "").toLowerCase();
    const odds = parseFloat(r.odds);
    if (v === "gagné" && !isNaN(odds)) {
      profit_units += (odds - 1);
    } else if (v === "perdu") {
      profit_units -= 1;
    }
  });
  const r_roi = r_settled > 0 ? (profit_units / r_settled * 100) : 0;

  return {
    principales: {
      total: p_total,
      winner_rate: p_winner_rate,
      winner_won: p_winner_won,
      winner_lost: p_winner_settled - p_winner_won,
      score_rate: p_score_rate,
      games_rate: p_games_rate,
    },
    recommandees: {
      total: r_total,
      win_rate: r_rate,
      won: r_won,
      lost: r_settled - r_won,
      roi_pct: r_roi,
      profit_units: profit_units,
    },
    raw_rows: rows,
  };
}


// Composant : zone de drop pour xlsx
function ImportZone({ onImport, t }) {
  const [dragActive, setDragActive] = useStateAI(false);
  const [importing, setImporting] = useStateAI(false);
  const [error, setError] = useStateAI(null);
  const [success, setSuccess] = useStateAI(null);
  const fileInputRef = useRefAI(null);

  const handleFile = async (file) => {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".xlsx") && !file.name.toLowerCase().endsWith(".xls")) {
      setError(t("aistats.import.errFormat", "Format invalide : seuls .xlsx et .xls sont acceptes"));
      return;
    }
    setImporting(true);
    setError(null);
    setSuccess(null);
    try {
      const rows = await parseSuiviVarionXlsx(file);
      if (rows.length === 0) {
        setError(t("aistats.import.errEmpty", "Aucun pari trouve dans le fichier"));
        setImporting(false);
        return;
      }

      // Stocker dans localStorage pour persistance
      try {
        localStorage.setItem("varion_imported_bets", JSON.stringify({
          rows: rows,
          imported_at: new Date().toISOString(),
          filename: file.name,
        }));
      } catch (e) { /* localStorage full */ }

      onImport(rows, file.name);
      setSuccess(`${rows.length} ${t("aistats.import.success", "paris importes avec succes")}`);
    } catch (e) {
      setError(`${t("aistats.import.errParse", "Erreur de lecture")} : ${e.message}`);
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="ai-panel mb-8" style={{ padding: 20 }}>
      <div className="label-uppercase text-ai mb-2">
        {t("aistats.import.title", "Importer un fichier de suivi")}
      </div>
      <div className="text-ink-3 mb-3" style={{ fontSize: 12 }}>
        {t("aistats.import.desc", "Glisse ton fichier suivi_varion.xlsx pour mettre a jour les stats. Les paris existants sont mis a jour, les nouveaux ajoutes.")}
      </div>

      <div
        onDragEnter={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragOver={(e) => { e.preventDefault(); }}
        onDragLeave={(e) => { e.preventDefault(); setDragActive(false); }}
        onDrop={(e) => {
          e.preventDefault();
          setDragActive(false);
          const f = e.dataTransfer.files[0];
          handleFile(f);
        }}
        onClick={() => fileInputRef.current && fileInputRef.current.click()}
        style={{
          border: `2px dashed ${dragActive ? "var(--ai)" : "var(--line)"}`,
          borderRadius: 14,
          padding: "32px 24px",
          textAlign: "center",
          cursor: "pointer",
          background: dragActive ? "rgba(167, 139, 250, 0.08)" : "var(--bg-2)",
          transition: "all 200ms",
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx,.xls"
          style={{ display: "none" }}
          onChange={(e) => handleFile(e.target.files[0])}
        />
        <div style={{ fontSize: 14, color: importing ? "var(--ink-3)" : "var(--ink)" }}>
          {importing
            ? t("aistats.import.loading", "Lecture du fichier en cours...")
            : (dragActive
                ? t("aistats.import.drop", "Relache le fichier ici")
                : t("aistats.import.cta", "Glisse ton .xlsx ici ou clique pour selectionner"))
          }
        </div>
      </div>

      {error && (
        <div className="mt-3" style={{
          padding: "10px 14px", borderRadius: 10,
          background: "rgba(255, 107, 156, 0.15)",
          borderLeft: "3px solid var(--loss)",
          color: "var(--loss)", fontSize: 13,
        }}>
          {error}
        </div>
      )}
      {success && (
        <div className="mt-3" style={{
          padding: "10px 14px", borderRadius: 10,
          background: "rgba(115, 245, 161, 0.15)",
          borderLeft: "3px solid var(--win)",
          color: "var(--win)", fontSize: 13,
        }}>
          {success}
        </div>
      )}
    </div>
  );
}


// Helper : badge couleur selon win rate
function getWinRateColor(pct) {
  if (pct >= 90) return "var(--win)";
  if (pct >= 70) return "var(--accent)";
  if (pct >= 55) return "var(--warn)";
  return "var(--loss)";
}

function getWinRateLabel(pct) {
  const t = window.t || ((k, f) => f || k);
  if (pct >= 90) return t("aistats.elite", "Au-dessus de l'objectif");
  if (pct >= 70) return t("aistats.solid", "Performance solide");
  if (pct >= 55) return t("aistats.average", "Performance moyenne");
  return t("aistats.toReview", "A surveiller");
}


// Composant : grand chiffre KPI
function KpiBlock({ label, value, suffix = "%", color, sublabel }) {
  return (
    <div className="card-flat" style={{ padding: 24, textAlign: "center" }}>
      <div className="label-uppercase" style={{ color: "var(--ink-3)" }}>{label}</div>
      <div style={{
        fontSize: 56, fontWeight: 700, color: color || "var(--ink)",
        letterSpacing: "-0.04em", marginTop: 8, lineHeight: 1,
      }}>
        {typeof value === "number" ? value.toFixed(1) : value}{suffix}
      </div>
      {sublabel && (
        <div style={{ fontSize: 12, color: "var(--ink-3)", marginTop: 6 }}>{sublabel}</div>
      )}
    </div>
  );
}


// Composant : breakdown table
function BreakdownTable({ title, data, labelKey, t }) {
  if (!data || data.length === 0) return null;
  return (
    <div className="card-flat mb-6" style={{ padding: 20 }}>
      <div className="label-uppercase text-ai mb-3">{title}</div>
      <table style={{ width: "100%", fontSize: 14 }}>
        <thead>
          <tr style={{ borderBottom: "1px solid var(--line)" }}>
            <th style={{ textAlign: "left", padding: "8px 4px", color: "var(--ink-3)", fontSize: 11, fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase" }}>{labelKey}</th>
            <th style={{ textAlign: "right", padding: "8px 4px", color: "var(--ink-3)", fontSize: 11, fontWeight: 600 }}>W/L</th>
            <th style={{ textAlign: "right", padding: "8px 4px", color: "var(--ink-3)", fontSize: 11, fontWeight: 600 }}>{t("aistats.winRate", "Win rate")}</th>
            <th style={{ textAlign: "right", padding: "8px 4px", color: "var(--ink-3)", fontSize: 11, fontWeight: 600 }}>ROI</th>
          </tr>
        </thead>
        <tbody>
          {data.map((d, i) => (
            <tr key={i} style={{ borderBottom: i < data.length - 1 ? "1px solid var(--line)" : "none" }}>
              <td style={{ padding: "10px 4px", textTransform: "capitalize", fontWeight: 500 }}>{d.group_value || "-"}</td>
              <td style={{ padding: "10px 4px", textAlign: "right", color: "var(--ink-2)" }}>{d.won}-{d.lost}</td>
              <td style={{ padding: "10px 4px", textAlign: "right", fontWeight: 700, color: getWinRateColor(d.win_rate_pct) }}>{d.win_rate_pct.toFixed(1)}%</td>
              <td style={{ padding: "10px 4px", textAlign: "right", fontWeight: 600, color: d.roi_pct > 0 ? "var(--win)" : (d.roi_pct < 0 ? "var(--loss)" : "var(--ink-3)") }}>
                {d.roi_pct > 0 ? "+" : ""}{d.roi_pct.toFixed(1)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}


// Composant : ligne historique
function HistoryRow({ bet, t }) {
  const won = bet.status === "won";
  const profit = bet.profit_units || 0;
  const date = bet.settled_at ? new Date(bet.settled_at).toLocaleDateString() : "-";
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 12, padding: "12px 14px",
      borderRadius: 12, background: "var(--bg-2)", marginBottom: 6,
      borderLeft: `3px solid ${won ? "var(--win)" : "var(--loss)"}`,
    }}>
      <span style={{
        display: "inline-flex", width: 24, height: 24, borderRadius: 6,
        alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700,
        background: won ? "rgba(115, 245, 161, 0.15)" : "rgba(255, 107, 156, 0.15)",
        color: won ? "var(--win)" : "var(--loss)",
      }}>{won ? "✓" : "✗"}</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 14, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {bet.market || bet.selection}
        </div>
        <div style={{ fontSize: 11, color: "var(--ink-3)", marginTop: 2 }}>
          {date} · {t("aistats.edge", "edge")} {bet.edge_pct > 0 ? "+" : ""}{(bet.edge_pct || 0).toFixed(1)}%
        </div>
      </div>
      <div style={{ textAlign: "right" }}>
        <div style={{ fontSize: 14, fontWeight: 700 }}>@ {(bet.odds || 0).toFixed(2)}</div>
        <div style={{ fontSize: 11, fontWeight: 600, color: profit > 0 ? "var(--win)" : "var(--loss)" }}>
          {profit > 0 ? "+" : ""}{profit.toFixed(2)}u
        </div>
      </div>
    </div>
  );
}


window.AiStats = function AiStats() {
  const [stats, setStats] = useStateAI(null);
  const [loading, setLoading] = useStateAI(true);
  const [error, setError] = useStateAI(null);
  const [, forceUpdate] = useStateAI({});
  const [importedStats, setImportedStats] = useStateAI(null);  // stats issues du xlsx
  const [importedFilename, setImportedFilename] = useStateAI("");

  const t = window.t || ((k, f) => f || k);

  // Re-render quand la langue change
  useEffectAI(() => {
    const handler = () => forceUpdate({});
    window.addEventListener("varion-lang-change", handler);
    return () => window.removeEventListener("varion-lang-change", handler);
  }, []);

  // Au chargement : recuperer un eventuel import stocke dans localStorage
  useEffectAI(() => {
    try {
      const raw = localStorage.getItem("varion_imported_bets");
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed.rows && parsed.rows.length > 0) {
          const computed = computeStatsFromRows(parsed.rows);
          setImportedStats(computed);
          setImportedFilename(parsed.filename || "imported.xlsx");
        }
      }
    } catch (e) { /* ignore */ }
  }, []);

  // Handler import xlsx
  const handleImport = (rows, filename) => {
    const computed = computeStatsFromRows(rows);
    setImportedStats(computed);
    setImportedFilename(filename);
  };

  // Clear import
  const clearImport = () => {
    setImportedStats(null);
    setImportedFilename("");
    try { localStorage.removeItem("varion_imported_bets"); } catch (e) {}
  };

  // Charger les stats : essai backend, fallback fichier statique
  useEffectAI(() => {
    async function loadStats() {
      const apiBase = (window.API_BASE !== undefined ? window.API_BASE : "");
      try {
        // Essai 1 : endpoint backend si dispo
        try {
          const r = await fetch(`${apiBase}/api/ai-stats`);
          if (r.ok) {
            const data = await r.json();
            setStats(data);
            setLoading(false);
            return;
          }
        } catch (e) { /* fallback */ }

        // Essai 2 : fichier statique
        const r2 = await fetch(`${apiBase}/ai_stats.json`);
        if (r2.ok) {
          const data = await r2.json();
          setStats(data);
        } else {
          setStats(null);
        }
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, []);

  if (loading) {
    return (
      <div className="container-app py-8 text-center">
        <div className="text-ink-3">{t("aistats.loading", "Chargement des stats...")}</div>
      </div>
    );
  }

  // Si pas de data (DB vide / fichier absent) : message + CTA + import zone
  if (!stats || !stats.global || stats.global.total === 0) {
    return (
      <div className="container-app py-8 fade-in">
        <h1 className="text-gradient-ai mb-2">{t("aistats.title", "Performance IA Varion")}</h1>
        <div className="text-ink-3 mb-8">{t("aistats.subtitle", "Suivi de la fiabilite de nos predictions")}</div>

        {/* IMPORT ZONE */}
        <ImportZone onImport={handleImport} t={t}/>

        {/* Si des donnees importees existent : afficher le bloc */}
        {importedStats && (
          <div className="ai-panel mb-8">
            <div className="ai-panel-header">
              <div className="ai-badge" style={{ background: "linear-gradient(135deg, var(--accent), var(--ai))" }}>XLS</div>
              <div style={{ flex: 1 }}>
                <div className="ai-label">{t("aistats.importedStats", "Stats depuis fichier importe")}</div>
                <div className="ai-time">{importedFilename}</div>
              </div>
              <button onClick={clearImport} className="btn-secondary" style={{ fontSize: 11, padding: "6px 12px" }}>
                {t("aistats.clearImport", "Effacer l'import")}
              </button>
            </div>
            <div className="mb-4">
              <div className="label-uppercase text-ai mb-3" style={{ fontSize: 11 }}>
                {t("aistats.importedPrincipales", "Predictions principales")}
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <KpiBlock label={t("aistats.totalBets", "Total paris")} value={importedStats.principales.total} suffix="" color="var(--ink)"/>
                <KpiBlock label={t("aistats.winRateWinner", "Win rate vainqueur")} value={importedStats.principales.winner_rate} color={getWinRateColor(importedStats.principales.winner_rate)} sublabel={`${importedStats.principales.winner_won}W / ${importedStats.principales.winner_lost}L`}/>
                <KpiBlock label={t("aistats.scoreExact", "% Score exact")} value={importedStats.principales.score_rate} color="var(--ai)"/>
                <KpiBlock label={t("aistats.gamesOver", "% Jeux Over")} value={importedStats.principales.games_rate} color="var(--accent)"/>
              </div>
            </div>
            <div>
              <div className="label-uppercase text-ai mb-3" style={{ fontSize: 11 }}>
                {t("aistats.importedRecommandees", "Paris recommandes")}
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                <KpiBlock label={t("aistats.totalBets", "Total paris")} value={importedStats.recommandees.total} suffix="" color="var(--ink)"/>
                <KpiBlock label={t("aistats.winRate", "Win rate")} value={importedStats.recommandees.win_rate} color={getWinRateColor(importedStats.recommandees.win_rate)} sublabel={`${importedStats.recommandees.won}W / ${importedStats.recommandees.lost}L`}/>
                <KpiBlock label="ROI" value={importedStats.recommandees.roi_pct} color={importedStats.recommandees.roi_pct > 0 ? "var(--win)" : "var(--loss)"} sublabel={`${importedStats.recommandees.profit_units > 0 ? "+" : ""}${importedStats.recommandees.profit_units.toFixed(2)}u`}/>
              </div>
            </div>
          </div>
        )}

        {!importedStats && (
          <div className="card-flat" style={{ padding: 60, textAlign: "center" }}>
            <div style={{ fontSize: 48, opacity: 0.2 }}>—</div>
            <div className="font-display" style={{ fontSize: 22, marginTop: 16 }}>
              {t("aistats.empty.title", "Aucun pari encore resolu")}
            </div>
            <div className="text-ink-3" style={{ marginTop: 8, maxWidth: 480, marginLeft: "auto", marginRight: "auto" }}>
              {t("aistats.empty.desc", "Les premiers paris IA seront affiches ici une fois les matchs joues. Reviens dans quelques jours pour voir nos performances en temps reel, ou importe ton fichier de suivi xlsx.")}
            </div>
          </div>
        )}
      </div>
    );
  }

  const g = stats.global;
  const targetWinRate = 90;
  const distanceFromTarget = g.win_rate_pct - targetWinRate;

  return (
    <div className="container-app py-8 fade-in">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-gradient-ai mb-2">{t("aistats.title", "Performance IA Varion")}</h1>
        <div className="text-ink-3">{t("aistats.subtitle", "Suivi de la fiabilite de nos predictions sur les paris a valeur")}</div>
      </div>

      {/* IMPORT ZONE */}
      <ImportZone onImport={handleImport} t={t}/>

      {/* Si des donnees importees existent : afficher le bloc dedie */}
      {importedStats && (
        <div className="ai-panel mb-8">
          <div className="ai-panel-header">
            <div className="ai-badge" style={{ background: "linear-gradient(135deg, var(--accent), var(--ai))" }}>XLS</div>
            <div style={{ flex: 1 }}>
              <div className="ai-label">{t("aistats.importedStats", "Stats depuis fichier importe")}</div>
              <div className="ai-time">{importedFilename}</div>
            </div>
            <button
              onClick={clearImport}
              className="btn-secondary"
              style={{ fontSize: 11, padding: "6px 12px" }}
            >
              {t("aistats.clearImport", "Effacer l'import")}
            </button>
          </div>

          {/* KPIs Predictions Principales */}
          <div className="mb-4">
            <div className="label-uppercase text-ai mb-3" style={{ fontSize: 11 }}>
              {t("aistats.importedPrincipales", "Predictions principales")}
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <KpiBlock
                label={t("aistats.totalBets", "Total paris")}
                value={importedStats.principales.total}
                suffix=""
                color="var(--ink)"
              />
              <KpiBlock
                label={t("aistats.winRateWinner", "Win rate vainqueur")}
                value={importedStats.principales.winner_rate}
                color={getWinRateColor(importedStats.principales.winner_rate)}
                sublabel={`${importedStats.principales.winner_won}W / ${importedStats.principales.winner_lost}L`}
              />
              <KpiBlock
                label={t("aistats.scoreExact", "% Score exact")}
                value={importedStats.principales.score_rate}
                color="var(--ai)"
              />
              <KpiBlock
                label={t("aistats.gamesOver", "% Jeux Over")}
                value={importedStats.principales.games_rate}
                color="var(--accent)"
              />
            </div>
          </div>

          {/* KPIs Paris Recommandes */}
          <div>
            <div className="label-uppercase text-ai mb-3" style={{ fontSize: 11 }}>
              {t("aistats.importedRecommandees", "Paris recommandes")}
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              <KpiBlock
                label={t("aistats.totalBets", "Total paris")}
                value={importedStats.recommandees.total}
                suffix=""
                color="var(--ink)"
              />
              <KpiBlock
                label={t("aistats.winRate", "Win rate")}
                value={importedStats.recommandees.win_rate}
                color={getWinRateColor(importedStats.recommandees.win_rate)}
                sublabel={`${importedStats.recommandees.won}W / ${importedStats.recommandees.lost}L`}
              />
              <KpiBlock
                label="ROI"
                value={importedStats.recommandees.roi_pct}
                color={importedStats.recommandees.roi_pct > 0 ? "var(--win)" : "var(--loss)"}
                sublabel={`${importedStats.recommandees.profit_units > 0 ? "+" : ""}${importedStats.recommandees.profit_units.toFixed(2)}u`}
              />
            </div>
          </div>
        </div>
      )}

      {/* HERO : Win rate gauge */}
      <div className="ai-panel mb-8">
        <div className="ai-panel-header">
          <div className="ai-badge">AI</div>
          <div>
            <div className="ai-label">{t("aistats.globalScore", "Score global de l'IA")}</div>
            <div className="ai-time">
              {t("aistats.basedOn", "Base sur")} {g.settled} {t("aistats.settledBets", "paris resolus")}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <KpiBlock
            label={t("aistats.winRate", "Win rate")}
            value={g.win_rate_pct}
            color={getWinRateColor(g.win_rate_pct)}
            sublabel={`${g.won}W / ${g.lost}L`}
          />
          <KpiBlock
            label="ROI"
            value={g.roi_pct}
            suffix="%"
            color={g.roi_pct > 0 ? "var(--win)" : "var(--loss)"}
            sublabel={`${g.profit_units > 0 ? "+" : ""}${g.profit_units}u`}
          />
          <KpiBlock
            label={t("aistats.avgEdge", "Edge moyen")}
            value={g.avg_edge_pct}
            color="var(--ai)"
            sublabel={t("aistats.modelVsBookies", "modele vs cotes")}
          />
          <KpiBlock
            label={t("aistats.totalBets", "Total paris")}
            value={g.total}
            suffix=""
            color="var(--ink)"
            sublabel={`${g.pending} ${t("aistats.pending", "en attente")}`}
          />
        </div>

        {/* Verdict */}
        <div style={{
          marginTop: 24, padding: "16px 18px", borderRadius: 14,
          background: "var(--bg-2)",
          borderLeft: `3px solid ${getWinRateColor(g.win_rate_pct)}`,
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
            <div>
              <div className="label-uppercase" style={{ color: getWinRateColor(g.win_rate_pct) }}>
                {getWinRateLabel(g.win_rate_pct)}
              </div>
              <div style={{ marginTop: 4, color: "var(--ink-2)", fontSize: 14 }}>
                {distanceFromTarget >= 0
                  ? t("aistats.aboveTarget", "Au-dessus de l'objectif 90%")
                  : `${Math.abs(distanceFromTarget).toFixed(1)} ${t("aistats.pointsBelowTarget", "points sous l'objectif 90%")}`}
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div className="label-uppercase" style={{ color: "var(--ink-3)" }}>{t("aistats.target", "Objectif")}</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: "var(--accent)" }}>{targetWinRate}%</div>
            </div>
          </div>
        </div>
      </div>

      {/* Breakdowns */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <BreakdownTable
          title={t("aistats.bySurface", "Par surface")}
          data={stats.by_surface || []}
          labelKey={t("perf.bySurface", "Surface")}
          t={t}
        />
        <BreakdownTable
          title={t("aistats.byTour", "Par tour")}
          data={stats.by_tour || []}
          labelKey="Tour"
          t={t}
        />
        <BreakdownTable
          title={t("aistats.byConfidence", "Par confiance modele")}
          data={stats.by_confidence || []}
          labelKey={t("aistats.confidence", "Confiance")}
          t={t}
        />
        <BreakdownTable
          title={t("aistats.bySport", "Par sport")}
          data={stats.by_sport || []}
          labelKey="Sport"
          t={t}
        />
      </div>

      {/* Historique recent */}
      {stats.recent_bets && stats.recent_bets.length > 0 && (
        <div className="mt-8">
          <div className="label-uppercase text-ai mb-3">{t("aistats.recentHistory", "Historique recent")}</div>
          <div>
            {stats.recent_bets.filter(b => b.status === "won" || b.status === "lost").slice(0, 20).map((bet, i) => (
              <HistoryRow key={i} bet={bet} t={t}/>
            ))}
          </div>
        </div>
      )}

      {/* CTA Souscrire */}
      <div className="card-varion mt-12" style={{ padding: 40, textAlign: "center" }}>
        <div className="label-uppercase text-ai mb-2">{t("aistats.cta.label", "Varion Pro")}</div>
        <h2 className="text-gradient-ai mb-3" style={{ fontSize: 32 }}>
          {t("aistats.cta.title", "Acces complet aux predictions IA")}
        </h2>
        <div className="text-ink-2 mb-6" style={{ maxWidth: 540, margin: "0 auto 24px" }}>
          {g.win_rate_pct >= 70
            ? t("aistats.cta.descGood", "Notre IA affiche un track record solide. Souscrivez pour acceder a tous les value bets en temps reel, l'historique complet, et les alertes mobile.")
            : t("aistats.cta.descNeutral", "Suivez les performances de notre IA, recevez les value bets en temps reel et l'historique complet en souscrivant a Varion Pro.")
          }
        </div>

        {/* Pitch points */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8" style={{ maxWidth: 720, margin: "0 auto 32px" }}>
          <div style={{ padding: 16, borderRadius: 12, background: "var(--bg-2)", border: "1px solid var(--line)" }}>
            <div style={{ fontSize: 24, fontWeight: 700, color: "var(--ai)" }}>{g.win_rate_pct.toFixed(0)}%</div>
            <div className="text-ink-3" style={{ fontSize: 12, marginTop: 4 }}>{t("aistats.cta.winRate", "Win rate IA")}</div>
          </div>
          <div style={{ padding: 16, borderRadius: 12, background: "var(--bg-2)", border: "1px solid var(--line)" }}>
            <div style={{ fontSize: 24, fontWeight: 700, color: g.roi_pct > 0 ? "var(--win)" : "var(--loss)" }}>
              {g.roi_pct > 0 ? "+" : ""}{g.roi_pct.toFixed(0)}%
            </div>
            <div className="text-ink-3" style={{ fontSize: 12, marginTop: 4 }}>{t("aistats.cta.roi", "ROI moyen")}</div>
          </div>
          <div style={{ padding: 16, borderRadius: 12, background: "var(--bg-2)", border: "1px solid var(--line)" }}>
            <div style={{ fontSize: 24, fontWeight: 700, color: "var(--accent)" }}>+{g.avg_edge_pct.toFixed(1)}%</div>
            <div className="text-ink-3" style={{ fontSize: 12, marginTop: 4 }}>{t("aistats.cta.edge", "Edge moyen")}</div>
          </div>
        </div>

        <button
          className="btn-primary"
          onClick={() => alert("Lien d'abonnement bientot dispo !")}
          style={{ fontSize: 15, padding: "14px 28px" }}
        >
          {t("aistats.cta.button", "Souscrire a Varion Pro")} →
        </button>

        <div className="text-ink-3 mt-4" style={{ fontSize: 11 }}>
          {t("aistats.cta.disclaimer", "Pariez de maniere responsable. 18+. La performance passee ne garantit pas les resultats futurs.")}
        </div>
      </div>
    </div>
  );
};
