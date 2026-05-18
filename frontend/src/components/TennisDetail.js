// ========== TENNIS MATCH DETAIL ==========
// Page detail d'un match tennis : ELO 3 surfaces, forme, predictions, value bets,
// + NOUVEAU : profil bio, stats career, perf par surface/rank, H2H specifiques.

const { useState: useStateTD, useEffect: useEffectTD } = React;


// Petit composant : barre de progression
function ProgressBar({ value, max = 100, color = "var(--accent)", label }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div>
      {label && (
        <div className="flex justify-between mb-1">
          <span className="font-mono text-[10px] text-[var(--text-muted)] uppercase tracking-wider">{label}</span>
          <span className="font-mono text-[10px] text-[var(--text-secondary)]">{value.toFixed(1)}%</span>
        </div>
      )}
      <div className="h-1.5 bg-[var(--border)] rounded-full overflow-hidden">
        <div
          className="h-full transition-all duration-500"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
    </div>
  );
}


// ========== HELPERS POUR LES NOUVELLES SECTIONS ==========

// Bloc bio profil joueur (taille, poids, main, etc.)
function BioBlock({ profile, color }) {
  if (!profile || Object.keys(profile).length === 0) return null;

  const t = window.t || ((k, f) => f || k);
  const plays = profile.plays || "";
  // ex "Right-Handed, Two-Handed Backhand"
  const isLefty = plays.toLowerCase().includes("left");
  const handLabel = isLefty
    ? t("profile.lefty", "Gaucher")
    : t("profile.righty", "Droitier");
  const backhandSuffix = plays.includes("Two-Handed")
    ? " " + t("profile.twoHandedBackhand", "(revers 2 mains)")
    : plays.includes("One-Handed")
      ? " " + t("profile.oneHandedBackhand", "(revers 1 main)")
      : "";

  return (
    <div className="mt-4 pt-4 border-t border-[var(--border)]">
      <div className="font-mono text-[10px] text-[var(--text-muted)] uppercase tracking-wider mb-2">{t("profile.title", "Profil").toUpperCase()}</div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 font-mono text-xs">
        {profile.height_cm > 0 && (
          <div>{profile.height_cm} {t("profile.height", "cm")}</div>
        )}
        {profile.weight_kg > 0 && (
          <div>{profile.weight_kg} {t("profile.weight", "kg")}</div>
        )}
        {plays && (
          <div className="col-span-2">{handLabel}{backhandSuffix}</div>
        )}
        {profile.turned_pro > 0 && (
          <div>{t("profile.proSince", "Pro depuis")} {profile.turned_pro}</div>
        )}
        {profile.status && profile.status !== "Active" && (
          <div className="text-[var(--text-muted)]">⚪ {profile.status}</div>
        )}
        {profile.birthplace && (
          <div className="col-span-2 truncate text-[var(--text-muted)]">{t("profile.bornIn", "Ne a")} {window.tBirthplace ? window.tBirthplace(profile.birthplace) : profile.birthplace}</div>
        )}
      </div>
    </div>
  );
}


// Composant : ligne de comparaison entre 2 joueurs (avec barres)
function StatRow({ label, valueA, valueB, suffix = "%", colorA, colorB, max = 100, formatVal }) {
  const fmt = formatVal || ((v) => `${v}${suffix}`);
  const totalForBar = max;

  // Determine qui est meilleur (plus de valeur = meilleur)
  const aBetter = valueA > valueB;
  const bBetter = valueB > valueA;

  return (
    <div className="grid grid-cols-7 gap-3 items-center py-1.5">
      {/* Joueur A */}
      <div className="col-span-3 flex items-center justify-end gap-2">
        <span className={`font-mono text-xs ${aBetter ? "font-bold" : "text-[var(--text-muted)]"}`} style={aBetter ? { color: colorA } : {}}>{fmt(valueA)}</span>
        <div className="w-16 h-1.5 bg-[var(--border)] rounded-full overflow-hidden flex flex-row-reverse">
          <div className="h-full" style={{ width: `${Math.min(100, (valueA / totalForBar) * 100)}%`, background: colorA }}/>
        </div>
      </div>
      {/* Label central */}
      <div className="col-span-1 text-center font-mono text-[10px] text-[var(--text-muted)] uppercase tracking-wide">{label}</div>
      {/* Joueur B */}
      <div className="col-span-3 flex items-center gap-2">
        <div className="w-16 h-1.5 bg-[var(--border)] rounded-full overflow-hidden">
          <div className="h-full" style={{ width: `${Math.min(100, (valueB / totalForBar) * 100)}%`, background: colorB }}/>
        </div>
        <span className={`font-mono text-xs ${bBetter ? "font-bold" : "text-[var(--text-muted)]"}`} style={bBetter ? { color: colorB } : {}}>{fmt(valueB)}</span>
      </div>
    </div>
  );
}


// Section : Comparaison stats career (service / retour / mental)
function CareerComparison({ pa, pb, colorA, colorB }) {
  const csA = pa.career_stats || {};
  const csB = pb.career_stats || {};

  // Si pas de career_stats des 2 cotes, on n'affiche pas cette section
  if (!csA.matches_played && !csB.matches_played) return null;

  return (
    <div className="card p-5 mb-8">
      <div className="font-mono text-[10px] text-[var(--accent)] uppercase tracking-widest mb-3">COMPARAISON CARRIERE</div>

      {/* Service */}
      <div className="mb-4">
        <div className="font-mono text-[10px] text-[var(--text-muted)] uppercase mb-2">SERVICE</div>
        <StatRow label="1ers serv" valueA={csA.first_serve_pct || 0} valueB={csB.first_serve_pct || 0} colorA={colorA} colorB={colorB}/>
        <StatRow label="Pts/1er" valueA={csA.won_first_serve_pct || 0} valueB={csB.won_first_serve_pct || 0} colorA={colorA} colorB={colorB}/>
        <StatRow label="Pts/2nd" valueA={csA.won_second_serve_pct || 0} valueB={csB.won_second_serve_pct || 0} colorA={colorA} colorB={colorB}/>
        <StatRow label="Aces/m" valueA={csA.aces_per_match || 0} valueB={csB.aces_per_match || 0} suffix="" max={20} colorA={colorA} colorB={colorB} formatVal={(v) => v.toFixed(1)}/>
      </div>

      {/* Retour */}
      <div className="mb-4">
        <div className="font-mono text-[10px] text-[var(--text-muted)] uppercase mb-2">RETOUR & BREAK</div>
        <StatRow label="Pts retour" valueA={csA.return_pts_won_pct || 0} valueB={csB.return_pts_won_pct || 0} colorA={colorA} colorB={colorB}/>
        <StatRow label="% break" valueA={csA.break_pts_converted_pct || 0} valueB={csB.break_pts_converted_pct || 0} colorA={colorA} colorB={colorB}/>
      </div>

      {/* Mental */}
      <div>
        <div className="font-mono text-[10px] text-[var(--text-muted)] uppercase mb-2">MENTAL & CLUTCH</div>
        <StatRow label="Win 1er set" valueA={csA.first_set_won_match_won_pct || 0} valueB={csB.first_set_won_match_won_pct || 0} colorA={colorA} colorB={colorB}/>
        <StatRow label="Remontada" valueA={csA.first_set_lost_match_won_pct || 0} valueB={csB.first_set_lost_match_won_pct || 0} colorA={colorA} colorB={colorB}/>
        <StatRow label="Set decisif" valueA={csA.deciding_set_win_pct || 0} valueB={csB.deciding_set_win_pct || 0} colorA={colorA} colorB={colorB}/>
        <StatRow label="Tiebreak" valueA={csA.tiebreak_win_pct || 0} valueB={csB.tiebreak_win_pct || 0} colorA={colorA} colorB={colorB}/>
      </div>

      {/* Win rate global */}
      <div className="mt-4 pt-3 border-t border-[var(--border)] grid grid-cols-2 gap-4 text-center">
        <div>
          <div className="font-mono text-[10px] text-[var(--text-muted)] uppercase">{(pa.name || "").split(" ").pop()}</div>
          <div className="font-display text-2xl mt-1" style={{ color: colorA }}>{(csA.win_rate_pct || 0).toFixed(0)}%</div>
          <div className="font-mono text-[10px] text-[var(--text-muted)]">{csA.matches_played || 0} matchs · {csA.titles || 0} titres</div>
        </div>
        <div>
          <div className="font-mono text-[10px] text-[var(--text-muted)] uppercase">{(pb.name || "").split(" ").pop()}</div>
          <div className="font-display text-2xl mt-1" style={{ color: colorB }}>{(csB.win_rate_pct || 0).toFixed(0)}%</div>
          <div className="font-mono text-[10px] text-[var(--text-muted)]">{csB.matches_played || 0} matchs · {csB.titles || 0} titres</div>
        </div>
      </div>
    </div>
  );
}


// Section : Performance recente (3 dernieres annees) par surface et niveau adversaire
function PerfBreakdownComparison({ pa, pb, colorA, colorB, currentSurface }) {
  const pbA = pa.perf_breakdown || {};
  const pbB = pb.perf_breakdown || {};

  if (!pbA.years_analyzed && !pbB.years_analyzed) return null;

  const renderRow = (label, dA, dB, highlight = false) => {
    const wrA = (dA && dA.total > 0) ? dA.win_rate : 0;
    const wrB = (dB && dB.total > 0) ? dB.win_rate : 0;
    return (
      <tr className={highlight ? "bg-[var(--accent)]/10" : ""}>
        <td className="py-1.5 font-mono text-[10px] text-[var(--text-muted)] uppercase">{label}</td>
        <td className="py-1.5 text-right font-mono text-xs">
          {dA && dA.total > 0 ? (
            <>
              <span style={{ color: colorA }} className="font-semibold">{wrA.toFixed(0)}%</span>
              <span className="text-[var(--text-muted)] ml-1">({dA.wins}-{dA.losses})</span>
            </>
          ) : <span className="text-[var(--text-muted)]">—</span>}
        </td>
        <td className="py-1.5 text-left font-mono text-xs pl-3">
          {dB && dB.total > 0 ? (
            <>
              <span style={{ color: colorB }} className="font-semibold">{wrB.toFixed(0)}%</span>
              <span className="text-[var(--text-muted)] ml-1">({dB.wins}-{dB.losses})</span>
            </>
          ) : <span className="text-[var(--text-muted)]">—</span>}
        </td>
      </tr>
    );
  };

  const yearsLbl = (pbA.years_analyzed || pbB.years_analyzed || []).join(", ");

  return (
    <div className="card p-5 mb-8">
      <div className="font-mono text-[10px] text-[var(--accent)] uppercase tracking-widest mb-1">BILAN RECENT</div>
      <div className="font-mono text-[10px] text-[var(--text-muted)] mb-3">Annees analysees : {yearsLbl}</div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Par surface */}
        <div>
          <div className="font-mono text-[10px] text-[var(--text-muted)] uppercase mb-2">PAR SURFACE</div>
          <table className="w-full">
            <tbody>
              {renderRow("HARD", pbA.hard, pbB.hard, currentSurface === "hard")}
              {renderRow("CLAY", pbA.clay, pbB.clay, currentSurface === "clay")}
              {renderRow("GRASS", pbA.grass, pbB.grass, currentSurface === "grass")}
              {renderRow("INDOOR", pbA.indoor_hard, pbB.indoor_hard, false)}
            </tbody>
          </table>
        </div>

        {/* Par niveau adversaire */}
        <div>
          <div className="font-mono text-[10px] text-[var(--text-muted)] uppercase mb-2">VS NIVEAU ADV</div>
          <table className="w-full">
            <tbody>
              {renderRow("vs Top 10", pbA.vs_top10, pbB.vs_top10)}
              {renderRow("vs Top 20", pbA.vs_top20, pbB.vs_top20)}
              {renderRow("vs Top 50", pbA.vs_top50, pbB.vs_top50)}
              {renderRow("vs Top 100", pbA.vs_top100, pbB.vs_top100)}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}


// Section : H2H specifique (par surface + mental)
function H2HSpecificBlock({ h2hSpecific, pa, pb, colorA, colorB, currentSurface }) {
  if (!h2hSpecific || !h2hSpecific.matches_count) return null;

  const total = h2hSpecific.matches_count || 0;
  const isSmallSample = total < 10;

  return (
    <div className="card p-5 mb-8">
      <div className="font-mono text-[10px] text-[var(--accent)] uppercase tracking-widest mb-3">H2H DETAILLE ({total} matchs)</div>

      {isSmallSample && (
        <div className="font-mono text-[10px] text-[var(--text-muted)] mb-3 italic">
          ⚠️ Echantillon faible : interpretations a relativiser
        </div>
      )}

      {/* Par surface dans leur H2H */}
      <div className="mb-4">
        <div className="font-mono text-[10px] text-[var(--text-muted)] uppercase mb-2">H2H PAR SURFACE</div>
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: "HARD", a: h2hSpecific.wins_a_hard, b: h2hSpecific.wins_b_hard, key: "hard" },
            { label: "CLAY", a: h2hSpecific.wins_a_clay, b: h2hSpecific.wins_b_clay, key: "clay" },
            { label: "GRASS", a: h2hSpecific.wins_a_grass, b: h2hSpecific.wins_b_grass, key: "grass" },
          ].map(s => {
            const t = (s.a || 0) + (s.b || 0);
            const isCurrent = currentSurface === s.key;
            return (
              <div key={s.key} className={`text-center p-2 rounded ${isCurrent ? "ring-1 ring-[var(--accent)] bg-[var(--accent)]/10" : ""}`}>
                <div className="font-mono text-[10px] text-[var(--text-muted)]">{s.label}</div>
                {t > 0 ? (
                  <div className="font-mono text-sm mt-1">
                    <span style={{ color: colorA }} className="font-semibold">{s.a || 0}</span>
                    <span className="text-[var(--text-muted)] mx-1">-</span>
                    <span style={{ color: colorB }} className="font-semibold">{s.b || 0}</span>
                  </div>
                ) : (
                  <div className="font-mono text-xs text-[var(--text-muted)] mt-1">jamais</div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Stats serve / mental dans leur H2H */}
      {h2hSpecific.first_serve_pct_a > 0 && (
        <div className="pt-3 border-t border-[var(--border)]">
          <div className="font-mono text-[10px] text-[var(--text-muted)] uppercase mb-2">PERF DANS LEURS DUELS</div>
          <StatRow label="1ers serv" valueA={h2hSpecific.first_serve_pct_a} valueB={h2hSpecific.first_serve_pct_b} colorA={colorA} colorB={colorB}/>
          <StatRow label="Set decis" valueA={h2hSpecific.deciding_set_pct_a} valueB={h2hSpecific.deciding_set_pct_b} colorA={colorA} colorB={colorB}/>
          <StatRow label="Tiebreak" valueA={h2hSpecific.tiebreak_pct_a} valueB={h2hSpecific.tiebreak_pct_b} colorA={colorA} colorB={colorB}/>
          {h2hSpecific.avg_match_time && (
            <div className="mt-2 font-mono text-[10px] text-[var(--text-muted)] text-center">
              ⏱️ Duree moyenne : {h2hSpecific.avg_match_time}
            </div>
          )}
        </div>
      )}
    </div>
  );
}



// Carte ELO d'un joueur avec breakdown par surface + bio
function PlayerEloCard({ player, color, isWinnerPredicted }) {
  const elo = player.elo || {};
  const rank = player.rank;

  return (
    <div className={`card p-5 ${isWinnerPredicted ? "ring-2 ring-[var(--accent)] ring-opacity-50" : ""}`}>
      <div className="flex items-start gap-3 mb-4">
        <div
          className="w-14 h-14 rounded-lg flex flex-col items-center justify-center text-white overflow-hidden"
          style={{ background: color }}
        >
          {player.country ? (
            <>
              <window.Flag country={player.country} width={36} height={24}/>
              <span className="font-mono text-[8px] mt-1">{player.country}</span>
            </>
          ) : (
            <span className="font-display text-xl">{(player.name || "?").slice(0, 3).toUpperCase()}</span>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-display text-xl truncate">{player.name}</div>
          <div className="font-mono text-xs text-[var(--text-muted)]">
            {rank ? `#${rank} ATP` : "Hors classement"} · {player.country || "?"}
          </div>
        </div>
      </div>

      <div className="space-y-2.5">
        <ProgressBar
          value={elo.global ? Math.min(100, ((elo.global - 1500) / 500) * 100) : 0}
          color={color}
          label="ELO Global"
        />
        <div className="font-mono text-xs text-right text-[var(--text-secondary)] -mt-1 mb-3">
          {(elo.global || 0).toFixed(0)}
        </div>

        <div className="grid grid-cols-3 gap-2 mt-3">
          <div className="text-center">
            <div className="font-mono text-[9px] text-[var(--text-muted)] uppercase tracking-wider">HARD</div>
            <div className="font-display text-lg mt-1">{(elo.hard || 0).toFixed(0)}</div>
          </div>
          <div className="text-center">
            <div className="font-mono text-[9px] text-[var(--text-muted)] uppercase tracking-wider">CLAY</div>
            <div className="font-display text-lg mt-1">{(elo.clay || 0).toFixed(0)}</div>
          </div>
          <div className="text-center">
            <div className="font-mono text-[9px] text-[var(--text-muted)] uppercase tracking-wider">GRASS</div>
            <div className="font-display text-lg mt-1">{(elo.grass || 0).toFixed(0)}</div>
          </div>
        </div>
      </div>

      {/* Forme recente */}
      {player.recent_results && player.recent_results.length > 0 && (
        <div className="mt-4 pt-4 border-t border-[var(--border)]">
          <div className="font-mono text-[10px] text-[var(--text-muted)] uppercase tracking-wider mb-2">FORME RECENTE</div>
          <div className="flex gap-1">
            {player.recent_results.slice(0, 5).map((r, i) => {
              // Supporte les 2 formats : booleen brut OU objet {result, won, opponent, score}
              const isWin = typeof r === "boolean"
                ? r
                : (r.result === "W" || r.won === true);
              const tooltip = typeof r === "object" && r.opponent
                ? `${r.date || ""} vs ${r.opponent} (${r.score || ""})`
                : (isWin ? "Victoire" : "Defaite");
              return (
                <div
                  key={i}
                  className={`form-pill ${isWin ? "form-W" : "form-L"}`}
                  title={tooltip}
                >
                  {isWin ? "W" : "L"}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* NOUVEAU : Bloc bio du joueur (taille, poids, main, etc.) */}
      <BioBlock profile={player.profile} color={color}/>
    </div>
  );
}


window.TennisDetail = function TennisDetail({ match, onBack }) {
  const [activeTab, setActiveTab] = useStateTD("overview");
  const [, forceTDUpdate] = useStateTD({});
  useEffectTD(() => {
    const h = () => forceTDUpdate({});
    window.addEventListener("varion-lang-change", h);
    return () => window.removeEventListener("varion-lang-change", h);
  }, []);

  if (!match) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-20 text-center">
        <div className="font-display text-3xl text-[var(--red)]">MATCH INTROUVABLE</div>
        <button className="btn mt-6" onClick={onBack}>← RETOUR</button>
      </div>
    );
  }

  const pa = match.player_a || {};
  const pb = match.player_b || {};
  const preds = match.predictions || {};
  const odds = match.odds || {};
  const valueBets = match.value_bets || [];
  const h2hSpecific = match.h2h_specific || {};

  // Normaliser les champs h2h (les noms varient selon la version du mapper)
  const h2hRaw = match.h2h || {};
  const h2h = {
    player_a_wins: h2hRaw.player_a_wins ?? h2hRaw.wins_a ?? 0,
    player_b_wins: h2hRaw.player_b_wins ?? h2hRaw.wins_b ?? 0,
    total: h2hRaw.total ?? ((h2hRaw.wins_a || 0) + (h2hRaw.wins_b || 0)),
    last_5_matches: h2hRaw.last_5_matches || [],
  };

  // Couleurs alignees sur la charte : violet IA (joueur A) + sky electric (joueur B)
  const tour = (match.tour || "ATP").toUpperCase();
  const colorA = "#A78BFA";  // var(--ai)
  const colorB = "#5B9DFF";  // var(--accent)

  // Surface (sans emoji, dot coloré)
  const surfaceData = (() => {
    const s = (match.surface || "hard").toLowerCase();
    if (s.includes("clay")) return { dot: "#E8743F", label: "CLAY", color: "#E8743F" };
    if (s.includes("grass")) return { dot: "#73F5A1", label: "GRASS", color: "#73F5A1" };
    if (s.includes("indoor")) return { dot: "#A78BFA", label: "INDOOR", color: "#A78BFA" };
    return { dot: "#5B9DFF", label: "HARD", color: "#5B9DFF" };
  })();

  // Vainqueur predit (probabilite la plus haute)
  const probA = preds.winner?.prob_a ?? 50;
  const probB = preds.winner?.prob_b ?? 50;
  const aWins = probA > probB;

  // Label des cotes : reelles (API directe) / The Odds API / indisponibles
  const oddsSource = (odds._source || "none");
  const bookmakerLabel = odds._bookmaker || "";
  const isRealOdds = (oddsSource === "api" || oddsSource === "the_odds_api") && odds["1"] && odds["2"];
  const cotesLabel = (
    <>
      {window.t("ai.bookmakerOdds", "Cotes bookmaker")}
      {oddsSource === "the_odds_api" && bookmakerLabel && (
        <span className="odds-source-badge" title={`Cotes en direct via The Odds API (${bookmakerLabel})`} style={{
          background: "rgba(115, 245, 161, 0.15)",
          border: "1px solid var(--win)",
          color: "var(--win)",
        }}>
          {bookmakerLabel.toUpperCase()}
        </span>
      )}
      {oddsSource === "api" && (
        <span className="odds-source-badge" title="Cotes API Tennis" style={{
          background: "rgba(91, 157, 255, 0.15)",
          border: "1px solid var(--accent)",
          color: "var(--accent)",
        }}>
          API
        </span>
      )}
      {!isRealOdds && (
        <span className="odds-source-badge" title="Aucun bookmaker ne propose de cotes pour ce match" style={{
          background: "rgba(255, 184, 77, 0.15)",
          border: "1px solid var(--warn)",
          color: "var(--warn)",
        }}>
          {window.t("ai.notAvailable", "INDISPO")}
        </span>
      )}
    </>
  );


  return (
    <div className="container-app py-8 fade-in">
      {/* Header avec retour */}
      <button className="btn-secondary mb-6" onClick={onBack}>← {window.t("match.back", "Retour")}</button>

      {/* HERO : nom du match + meta */}
      <div className="mb-8">
        <div className="label-uppercase text-ai mb-2">
          {tour}{match.tournament ? " · " + match.tournament : ""}{match.round ? " · " + (window.tApi ? window.tApi(match.round) : match.round) : ""}
        </div>
        <h1 className="text-gradient-ai" style={{
          fontSize: "clamp(36px, 5vw, 56px)", fontWeight: 700, letterSpacing: "-0.04em", lineHeight: 1.05,
        }}>
          {pa.name} <span style={{ color: "var(--ink-3)", fontWeight: 400, fontSize: "0.7em" }}>vs</span> {pb.name}
        </h1>
        <div className="mt-4 flex items-center flex-wrap gap-3 text-sm" style={{ color: "var(--ink-2)" }}>
          {(() => {
            const ts = match.start_timestamp_ms;
            if (ts && ts > 0) {
              const dt = new Date(ts);
              const dateStr = dt.toLocaleDateString(undefined, { day: "2-digit", month: "long", year: "numeric" });
              return <span>{dateStr}</span>;
            }
            return <span>{match.date}</span>;
          })()}
          <span style={{ color: surfaceData.color, display: "inline-flex", alignItems: "center", gap: 6 }}>
            <span style={{ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: surfaceData.dot, boxShadow: `0 0 6px ${surfaceData.dot}` }}/>
            {window.tApi ? window.tApi(surfaceData.label.toLowerCase()).toUpperCase() : surfaceData.label}
          </span>
          <span className="tag">{window.tApi ? window.tApi(match.format || "BO3") : (match.format || "BO3")}</span>
          {match.tournament_type && match.tournament_type !== "Other" && (
            <span className="badge-tier">{window.tApi ? window.tApi(match.tournament_type) : match.tournament_type}</span>
          )}
        </div>
        <div className="mt-3 text-xs" style={{ color: "var(--ink-3)" }}>
          {window.t("match.timeIndicative", "Horaire exact confirme par le bookmaker quelques heures avant le match")}
        </div>
      </div>

      {/* TABS */}
      <div className="tab-bar">
        <button
          className={`tab-btn ${activeTab === "overview" ? "active" : ""}`}
          onClick={() => setActiveTab("overview")}
        >
          {window.t("tab.overview", "Vue d'ensemble")}
        </button>
        <button
          className={`tab-btn ${activeTab === "stats" ? "active" : ""}`}
          onClick={() => setActiveTab("stats")}
        >
          {window.t("tab.stats", "Stats")}
        </button>
        <button
          className={`tab-btn ${activeTab === "h2h" ? "active" : ""}`}
          onClick={() => setActiveTab("h2h")}
        >
          {window.t("tab.h2h", "H2H")}
        </button>
      </div>

      {/* === ONGLET 1 : VUE D'ENSEMBLE === */}
      {activeTab === "overview" && (
        <div className="fade-in">
          {/* AI VERDICT (proeminent) */}
          {(() => {
            const lang = window.__VARION_LANG || "fr";
            const summary = (match.summaries && match.summaries[lang]) || match.summary;
            if (!summary) return null;
            return (
              <div className="ai-panel mb-8">
                <div className="ai-panel-header">
                  <div className="ai-badge">AI</div>
                  <div>
                    <div className="ai-label">{window.t("ai.varionAi", "Varion AI")}</div>
                    <div className="ai-time">{window.t("ai.completeAnalysis", "Analyse complete · mise a jour il y a peu")}</div>
                  </div>
                </div>
                <div className="ai-verdict">
                  {typeof summary === "string" ? summary : JSON.stringify(summary)}
                </div>
              </div>
            );
          })()}

          {/* 3-COL : joueur A | predictions centrales | joueur B */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-8">
            <PlayerEloCard player={pa} color={colorA} isWinnerPredicted={aWins} />

            {/* Centre : prediction vainqueur + cotes + total games + h2h */}
            <div className="card-flat" style={{ padding: 20 }}>
              <div className="label-uppercase mb-3 text-center" style={{ color: "var(--ink-3)" }}>
                {window.t("ai.predictionWinner", "Prediction vainqueur")}
              </div>
              <div className="space-y-3 mb-6">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span style={{ color: colorA, fontWeight: 600 }}>{pa.name?.split(" ").pop() || "A"}</span>
                    <span className="font-data" style={{ color: colorA, fontWeight: 600 }}>{probA.toFixed(1)}%</span>
                  </div>
                  <div className="prob-bar"><div className="prob-bar-fill" style={{ width: `${probA}%`, background: colorA }}/></div>
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span style={{ color: colorB, fontWeight: 600 }}>{pb.name?.split(" ").pop() || "B"}</span>
                    <span className="font-data" style={{ color: colorB, fontWeight: 600 }}>{probB.toFixed(1)}%</span>
                  </div>
                  <div className="prob-bar"><div className="prob-bar-fill" style={{ width: `${probB}%`, background: colorB }}/></div>
                </div>
              </div>

              {/* Cotes */}
              <div style={{ borderTop: "1px solid var(--line)", paddingTop: 14, marginBottom: 14 }}>
                <div className="label-uppercase mb-2" style={{ color: "var(--ink-3)" }}>{cotesLabel}</div>
                {(!odds["1"] || !odds["2"] || odds["1"] < 1.01) ? (
                  <div className="text-center" style={{ padding: "14px 8px", color: "var(--ink-3)", fontStyle: "italic", fontSize: 13 }}>
                    {window.t("ai.oddsUnavailable", "Cote indisponible chez les bookmakers")}
                  </div>
                ) : (
                  <div className="grid grid-cols-2 gap-3">
                    <div className="text-center" style={{ background: "var(--bg-0)", padding: "10px 8px", borderRadius: 12, border: "1px solid var(--line)" }}>
                      <div className="text-xs" style={{ color: "var(--ink-3)" }}>{(pa.name || "?").split(" ").pop()}</div>
                      <div className="font-data" style={{ fontSize: 24, fontWeight: 700, marginTop: 4 }}>{odds["1"].toFixed(2)}</div>
                    </div>
                    <div className="text-center" style={{ background: "var(--bg-0)", padding: "10px 8px", borderRadius: 12, border: "1px solid var(--line)" }}>
                      <div className="text-xs" style={{ color: "var(--ink-3)" }}>{(pb.name || "?").split(" ").pop()}</div>
                      <div className="font-data" style={{ fontSize: 24, fontWeight: 700, marginTop: 4 }}>{odds["2"].toFixed(2)}</div>
                    </div>
                  </div>
                )}
              </div>

              {/* Total games */}
              {preds.total_games && (
                <div style={{ borderTop: "1px solid var(--line)", paddingTop: 14, marginBottom: 14 }}>
                  <div className="label-uppercase mb-1" style={{ color: "var(--ink-3)" }}>{window.t("ai.totalGamesPredicted", "Total games prevu")}</div>
                  <div className="font-data" style={{ fontSize: 24, fontWeight: 700 }}>
                    {preds.total_games.expected_total?.toFixed(1) || preds.total_games.expected?.toFixed(1) || "?"}
                  </div>
                </div>
              )}

              {/* H2H mini */}
              {h2h && h2h.total > 0 && (
                <div style={{ borderTop: "1px solid var(--line)", paddingTop: 14 }}>
                  <div className="label-uppercase mb-2" style={{ color: "var(--ink-3)" }}>{window.t("ai.headToHead", "Face-a-face")}</div>
                  <div className="flex items-center justify-around">
                    <div className="text-center">
                      <div className="font-data" style={{ fontSize: 22, fontWeight: 700, color: colorA }}>{h2h.player_a_wins || 0}</div>
                      <div className="text-xs" style={{ color: "var(--ink-3)" }}>{(pa.name || "").split(" ").pop()}</div>
                    </div>
                    <div className="text-center" style={{ color: "var(--ink-3)" }}>
                      <div className="font-data" style={{ fontSize: 18 }}>{h2h.total}</div>
                      <div className="text-xs">{window.t("ai.matches", "matchs")}</div>
                    </div>
                    <div className="text-center">
                      <div className="font-data" style={{ fontSize: 22, fontWeight: 700, color: colorB }}>{h2h.player_b_wins || 0}</div>
                      <div className="text-xs" style={{ color: "var(--ink-3)" }}>{(pb.name || "").split(" ").pop()}</div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <PlayerEloCard player={pb} color={colorB} isWinnerPredicted={!aWins} />
          </div>

          {/* ENCART CONDITIONS DE JEU (météo) */}
          {preds.weather && (() => {
            const w = preds.weather;
            const archetypes = {
              big_server: "Grand serveur",
              defender: "Défenseur",
              serve_volleyer: "Serveur-volleyeur",
              baseliner: "Fond de court",
              unknown: "—",
            };
            const fmt = (n, suffix = "") => (n === null || n === undefined) ? "—" : `${Math.round(n)}${suffix}`;
            const fmtDecimal = (n, suffix = "") => (n === null || n === undefined) ? "—" : `${n.toFixed(1)}${suffix}`;

            return (
              <div style={{
                background: "var(--surface-1)",
                border: "1px solid var(--line)",
                borderRadius: 12,
                padding: 20,
                marginBottom: 16,
              }}>
                <div className="flex items-center" style={{ marginBottom: 16, gap: 12 }}>
                  <div style={{
                    width: 40, height: 40, borderRadius: 10,
                    background: "linear-gradient(135deg, #60a5fa, #3b82f6)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    color: "white", fontWeight: 700, fontSize: 18,
                  }}>🌡️</div>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 700, letterSpacing: 0.5, color: "var(--accent-2)" }}>CONDITIONS DE JEU</div>
                    <div style={{ fontSize: 12, color: "var(--ink-3)" }}>Météo & impact sur les prédictions</div>
                  </div>
                </div>

                {/* Stats météo : 4 colonnes */}
                <div style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(4, 1fr)",
                  gap: 12,
                  marginBottom: 14,
                }}>
                  <div style={{ textAlign: "center", padding: "10px 8px", background: "var(--surface-2)", borderRadius: 8 }}>
                    <div style={{ fontSize: 11, color: "var(--ink-3)", marginBottom: 4 }}>🌡️ TEMPÉRATURE</div>
                    <div className="font-data" style={{ fontSize: 18, fontWeight: 700 }}>{fmt(w.temp_c, "°C")}</div>
                  </div>
                  <div style={{ textAlign: "center", padding: "10px 8px", background: "var(--surface-2)", borderRadius: 8 }}>
                    <div style={{ fontSize: 11, color: "var(--ink-3)", marginBottom: 4 }}>💧 HUMIDITÉ</div>
                    <div className="font-data" style={{ fontSize: 18, fontWeight: 700 }}>{fmt(w.humidity_pct, "%")}</div>
                  </div>
                  <div style={{ textAlign: "center", padding: "10px 8px", background: "var(--surface-2)", borderRadius: 8 }}>
                    <div style={{ fontSize: 11, color: "var(--ink-3)", marginBottom: 4 }}>💨 VENT MAX</div>
                    <div className="font-data" style={{ fontSize: 18, fontWeight: 700 }}>{fmt(w.wind_max_kmh, " km/h")}</div>
                  </div>
                  <div style={{ textAlign: "center", padding: "10px 8px", background: "var(--surface-2)", borderRadius: 8 }}>
                    <div style={{ fontSize: 11, color: "var(--ink-3)", marginBottom: 4 }}>🏔️ ALTITUDE</div>
                    <div className="font-data" style={{ fontSize: 18, fontWeight: 700 }}>{fmt(w.altitude_m, " m")}</div>
                  </div>
                </div>

                {/* Vitesse balle effective */}
                {w.ball_speed_change_pct !== undefined && w.ball_speed_change_pct !== 0 && (
                  <div style={{
                    background: "var(--surface-2)",
                    borderRadius: 8,
                    padding: "10px 14px",
                    marginBottom: 14,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}>
                    <div style={{ fontSize: 13, color: "var(--ink-2)" }}>⚾ Vitesse balle effective</div>
                    <div className="font-data" style={{
                      fontSize: 16,
                      fontWeight: 700,
                      color: w.ball_speed_change_pct > 0 ? "var(--success)" : "var(--accent-2)",
                    }}>
                      {w.ball_speed_change_pct > 0 ? "+" : ""}{fmtDecimal(w.ball_speed_change_pct, "%")}
                    </div>
                  </div>
                )}

                {/* Court Pace Index (CPI) */}
                {w.cpi !== undefined && (
                  <div style={{
                    background: "var(--surface-2)",
                    borderRadius: 8,
                    padding: "10px 14px",
                    marginBottom: 14,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}>
                    <div style={{ fontSize: 13, color: "var(--ink-2)" }}>🏟️ Vitesse du court (CPI)</div>
                    <div className="font-data" style={{
                      fontSize: 14,
                      fontWeight: 700,
                      color: w.cpi >= 40 ? "#f87171" : w.cpi < 25 ? "#60a5fa" : "var(--ink-2)",
                    }}>
                      {w.cpi} · {w.cpi_label || "—"}
                    </div>
                  </div>
                )}

                {/* Impact joueurs */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                  <div style={{
                    background: "var(--surface-2)",
                    borderRadius: 8,
                    padding: 12,
                    borderLeft: `3px solid ${colorA}`,
                  }}>
                    <div style={{ fontSize: 12, color: "var(--ink-3)", marginBottom: 4 }}>
                      {(pa.name || "").split(" ").pop()} • {archetypes[w.archetype_a] || "—"}
                    </div>
                    <div className="font-data" style={{
                      fontSize: 18,
                      fontWeight: 700,
                      color: (w.bonus_a_pct || 0) > 0 ? "var(--success)" : (w.bonus_a_pct || 0) < 0 ? "#ef4444" : "var(--ink-2)",
                    }}>
                      {(w.bonus_a_pct || 0) > 0 ? "+" : ""}{fmtDecimal(w.bonus_a_pct, "pp")}
                    </div>
                    {w.reasons_a && w.reasons_a.length > 0 && (
                      <div style={{ marginTop: 6, fontSize: 11, color: "var(--ink-3)", lineHeight: 1.5 }}>
                        {w.reasons_a.map((r, i) => <div key={i}>• {r}</div>)}
                      </div>
                    )}
                  </div>
                  <div style={{
                    background: "var(--surface-2)",
                    borderRadius: 8,
                    padding: 12,
                    borderLeft: `3px solid ${colorB}`,
                  }}>
                    <div style={{ fontSize: 12, color: "var(--ink-3)", marginBottom: 4 }}>
                      {(pb.name || "").split(" ").pop()} • {archetypes[w.archetype_b] || "—"}
                    </div>
                    <div className="font-data" style={{
                      fontSize: 18,
                      fontWeight: 700,
                      color: (w.bonus_b_pct || 0) > 0 ? "var(--success)" : (w.bonus_b_pct || 0) < 0 ? "#ef4444" : "var(--ink-2)",
                    }}>
                      {(w.bonus_b_pct || 0) > 0 ? "+" : ""}{fmtDecimal(w.bonus_b_pct, "pp")}
                    </div>
                    {w.reasons_b && w.reasons_b.length > 0 && (
                      <div style={{ marginTop: 6, fontSize: 11, color: "var(--ink-3)", lineHeight: 1.5 }}>
                        {w.reasons_b.map((r, i) => <div key={i}>• {r}</div>)}
                      </div>
                    )}
                  </div>
                </div>

                {/* Conditions extremes ? */}
                {w.extreme_conditions && (
                  <div style={{
                    marginTop: 14,
                    padding: "10px 14px",
                    background: "rgba(239, 68, 68, 0.1)",
                    border: "1px solid rgba(239, 68, 68, 0.3)",
                    borderRadius: 8,
                  }}>
                    <div style={{ fontSize: 12, color: "#f87171", fontWeight: 700, marginBottom: 4 }}>
                      ⚠️ Conditions extrêmes — confiance réduite
                    </div>
                    {w.extreme_reasons && w.extreme_reasons.map((r, i) => (
                      <div key={i} style={{ fontSize: 11, color: "var(--ink-3)" }}>• {r}</div>
                    ))}
                  </div>
                )}
              </div>
            );
          })()}

          {/* VALUE BETS / PREDICTIONS IA */}
          {valueBets.length > 0 && (() => {
            const isModelOnly = valueBets.every(b => b.type === "model_pick" || b.confidence === "model_only");
            const labelKey = isModelOnly ? "ai.modelPicks" : "ai.valueBets";
            const labelDefault = isModelOnly ? "Predictions IA" : "Paris a valeur";
            const subLabel = isModelOnly
              ? window.t("ai.modelPickDesc", "Prediction du modele (sans cote bookmaker)")
              : `${valueBets.length} value bet${valueBets.length > 1 ? "s" : ""} detecte${valueBets.length > 1 ? "s" : ""}`;
            return (
              <div className="ai-panel mb-8">
                <div className="ai-panel-header">
                  <div className="ai-badge">{isModelOnly ? "AI" : "VB"}</div>
                  <div>
                    <div className="ai-label">{window.t(labelKey, labelDefault)}</div>
                    <div className="ai-time">{subLabel}</div>
                  </div>
                </div>
                <div>
                  {valueBets.map((b, i) => {
                    const isModelPick = b.type === "model_pick" || b.confidence === "model_only";
                    const isHot = !isModelPick && b.edge_pct >= 10;
                    return (
                      <div key={i} className={`value-bet-item ${isHot ? "hot" : ""}`}>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: 600, fontSize: 14 }}>
                            {b.market}
                            {isModelPick && (
                              <span className="odds-source-badge" style={{ marginLeft: 8, borderColor: "var(--ai)", color: "var(--ai)" }}>
                                {window.t("ai.modelPick", "Pick IA")}
                              </span>
                            )}
                          </div>
                          {b.explanation && <div className="text-xs mt-1" style={{ color: "var(--ink-3)" }}>{b.explanation}</div>}
                        </div>
                        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                          {isModelPick ? (
                            <span style={{ color: "var(--ai)", fontWeight: 600, fontSize: 13 }}>{b.model_prob.toFixed(0)}%</span>
                          ) : (
                            <span className={`value-bet-edge ${isHot ? "hot" : ""}`}>+{b.edge_pct.toFixed(1)}%</span>
                          )}
                          <span className="value-bet-odd">{b.odds && b.odds >= 1.01 ? b.odds.toFixed(2) : "—"}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })()}

          {/* SETS PREDICTION */}
          {preds.sets_score && (
            <div className="card-flat mb-8" style={{ padding: 20 }}>
              <div className="label-uppercase text-ai mb-3">{window.t("ai.mostProbableScore", "Score le plus probable")}</div>
              <div className="space-y-2">
                {[
                  { label: `2-0 ${(pa.name || "").split(" ").pop()}`, value: preds.sets_score["2-0_a"] || 0, color: colorA },
                  { label: `2-1 ${(pa.name || "").split(" ").pop()}`, value: preds.sets_score["2-1_a"] || 0, color: colorA },
                  { label: `2-1 ${(pb.name || "").split(" ").pop()}`, value: preds.sets_score["2-1_b"] || 0, color: colorB },
                  { label: `2-0 ${(pb.name || "").split(" ").pop()}`, value: preds.sets_score["2-0_b"] || 0, color: colorB },
                ].sort((a, b) => b.value - a.value).map((s, i) => (
                  <div key={i}>
                    <div className="flex justify-between text-xs mb-1">
                      <span style={i === 0 ? { fontWeight: 700 } : {}}>{s.label}</span>
                      <span className="font-data">{s.value.toFixed(1)}%</span>
                    </div>
                    <div className="prob-bar"><div className="prob-bar-fill" style={{ width: `${s.value}%`, background: s.color }}/></div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* === ONGLET 2 : STATS === */}
      {activeTab === "stats" && (
        <div className="fade-in">
          <CareerComparison pa={pa} pb={pb} colorA={colorA} colorB={colorB}/>
          <PerfBreakdownComparison
            pa={pa} pb={pb} colorA={colorA} colorB={colorB}
            currentSurface={(match.surface || "hard").toLowerCase()}
          />
        </div>
      )}

      {/* === ONGLET 3 : H2H === */}
      {activeTab === "h2h" && (
        <div className="fade-in">
          <H2HSpecificBlock
            h2hSpecific={h2hSpecific}
            pa={pa} pb={pb} colorA={colorA} colorB={colorB}
            currentSurface={(match.surface || "hard").toLowerCase()}
          />

          {/* 5 derniers H2H matchs */}
          {h2h.last_5_matches && h2h.last_5_matches.length > 0 && (
            <div className="card-flat" style={{ padding: 20 }}>
              <div className="label-uppercase text-ai mb-3">{window.t("h2h.last5", "5 derniers face-a-face")}</div>
              <div>
                {h2h.last_5_matches.map((m, i) => {
                  const winner = m.winner === "A" ? pa.name : (m.winner === "B" ? pb.name : "Egalite");
                  const winnerColor = m.winner === "A" ? colorA : colorB;
                  return (
                    <div key={i} style={{
                      display: "flex", alignItems: "center", gap: 16,
                      padding: "10px 0", borderBottom: i < h2h.last_5_matches.length - 1 ? "1px solid var(--line)" : "none",
                    }}>
                      <span className="font-data text-xs" style={{ color: "var(--ink-3)", width: 96 }}>{m.date}</span>
                      <span className="font-data text-sm" style={{ flex: 1 }}>{m.result}</span>
                      <span style={{ color: winnerColor, fontSize: 13, fontWeight: 600 }}>{winner.split(" ").pop()}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {(!h2h.last_5_matches || h2h.last_5_matches.length === 0) && (!h2hSpecific || !h2hSpecific.matches_count) && (
            <div className="card-flat text-center" style={{ padding: 40 }}>
              <div style={{ fontSize: 16, color: "var(--ink-3)" }}>{window.t("h2h.empty", "Aucun face-a-face precedent enregistre.")}</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
