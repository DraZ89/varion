// Match Detail - vue complète d'un match

const { useState: useStateMD, useEffect: useEffectMD } = React;

window.MatchDetail = function MatchDetail({ matchId, onBack }) {
  const [data, setData] = useStateMD(null);
  const [loading, setLoading] = useStateMD(true);
  const [error, setError] = useStateMD(null);

  useEffectMD(() => {
    setLoading(true);
    window.api.match(matchId)
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, [matchId]);

  if (loading) return <window.Loading label="Analyse du match" />;
  if (error) return (
    <div className="text-center py-20 text-[var(--red)] font-mono">Erreur: {error}</div>
  );
  if (!data) return null;

  const { teams, predictions, value_bets, h2h, summary, confidence_score } = data;
  const home = teams.home;
  const away = teams.away;

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-8 fade-in">

      {/* Back button */}
      <div className="flex items-center justify-between">
        <button className="btn" onClick={onBack}>← Retour</button>
        <div className="font-mono text-[10px] text-[var(--text-muted)] uppercase tracking-widest">
          ID: {data.id}
        </div>
      </div>

      {/* HEADER MATCH */}
      <div className="card p-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <span className="font-mono text-[10px] uppercase tracking-widest text-[var(--accent)]">
              {data.competition}
            </span>
            <div className="flex items-center gap-3 mt-1">
              <span className="font-mono text-xs text-[var(--text-muted)]">
                {window.helpers.formatDate(data.date)} · {data.kickoff} · {data.venue}
              </span>
              {data.is_derby && <span className="tag tag-amber">DERBY</span>}
              {data.stakes === "high" && <span className="tag tag-red">ENJEU FORT</span>}
            </div>
          </div>
          <div className="text-right">
            <div className="stat-label">Arbitre</div>
            <div className="font-mono text-sm mt-1">{data.referee}</div>
          </div>
        </div>

        <div className="grid grid-cols-3 items-center gap-6 mb-8">
          <div className="flex flex-col items-center gap-3">
            <window.TeamLogo team={home.info} size={88} />
            <div className="text-center">
              <div className="font-display text-3xl">{home.info.name}</div>
              <div className="font-mono text-[11px] text-[var(--text-muted)]">
                #{home.info.rank} · {home.info.points} PTS
              </div>
              <div className="mt-2"><window.FormPills form={home.info.form_10} /></div>
            </div>
          </div>

          <div className="text-center">
            <div className="font-display text-6xl text-[var(--accent)]">
              {predictions.result.most_likely_score}
            </div>
            <div className="font-mono text-[10px] text-[var(--text-muted)] uppercase tracking-widest mt-1">
              SCORE LE PLUS PROBABLE · {predictions.result.most_likely_score_prob.toFixed(1)}%
            </div>
            <div className="mt-3 flex items-center justify-center gap-2 text-[10px] font-mono text-[var(--text-muted)] uppercase tracking-widest">
              <span>λH = {predictions.result.lambda_home}</span>
              <span>·</span>
              <span>λA = {predictions.result.lambda_away}</span>
            </div>
          </div>

          <div className="flex flex-col items-center gap-3">
            <window.TeamLogo team={away.info} size={88} />
            <div className="text-center">
              <div className="font-display text-3xl">{away.info.name}</div>
              <div className="font-mono text-[11px] text-[var(--text-muted)]">
                #{away.info.rank} · {away.info.points} PTS
              </div>
              <div className="mt-2"><window.FormPills form={away.info.form_10} /></div>
            </div>
          </div>
        </div>

        <div className="mb-4">
          <window.ProbaGauge
            home={predictions.result.prob_home_win}
            draw={predictions.result.prob_draw}
            away={predictions.result.prob_away_win}
            homeLabel={`${home.info.short} (1)`}
            awayLabel={`${away.info.short} (2)`}
          />
        </div>

        <window.ConfidenceBar score={confidence_score} />
      </div>

      {/* ============ SECTION 1 : RÉSUMÉ IA ============ */}
      <div>
        <div className="section-header">
          <span className="section-num">01 /</span>
          <h2>SYNTHÈSE</h2>
          <span className="font-mono text-[10px] text-[var(--text-muted)] uppercase tracking-widest ml-auto">
            ANALYSE GÉNÉRÉE
          </span>
        </div>
        <div className="card p-6">
          <p className="text-[var(--text-primary)] leading-relaxed text-base" style={{ fontFamily: "Manrope" }}>
            {summary}
          </p>
        </div>
      </div>

      {/* ============ SECTION 2 : ANALYSE ÉQUIPES ============ */}
      <div>
        <div className="section-header">
          <span className="section-num">02 /</span>
          <h2>ANALYSE ÉQUIPES</h2>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <window.TeamScoreCard team={home} title="DOMICILE" />
          <window.TeamScoreCard team={away} title="EXTÉRIEUR" />
        </div>
      </div>

      {/* ============ SECTION 3 : COMPOSITIONS ============ */}
      <div>
        <div className="section-header">
          <span className="section-num">03 /</span>
          <h2>COMPOSITIONS PROBABLES (XI TYPE)</h2>
          <span className="font-mono text-[10px] text-[var(--text-muted)] ml-auto">
            BASÉ SUR LES MINUTES JOUÉES
          </span>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <window.LineupCard team={home} />
          <window.LineupCard team={away} />
        </div>
      </div>

      {/* ============ SECTION 4 : JOUEURS CLÉS ============ */}
      <div>
        <div className="section-header">
          <span className="section-num">04 /</span>
          <h2>★ JOUEURS À SUIVRE</h2>
          <span className="font-mono text-[10px] text-[var(--accent)] ml-auto">
            PROFILS DÉCISIFS
          </span>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <window.KeyPlayersCard players={home.key_players} teamName={home.info.short} />
          <window.KeyPlayersCard players={away.key_players} teamName={away.info.short} />
        </div>
      </div>

      {/* ============ SECTION 5 : GARDIENS ============ */}
      <div>
        <div className="section-header">
          <span className="section-num">05 /</span>
          <h2>GARDIENS &amp; CLEAN SHEETS</h2>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <window.GoalkeeperCard
            gk={home.goalkeeper}
            cs_prob={predictions.clean_sheet.prob_cs_home}
            teamName={home.info.short}
          />
          <window.GoalkeeperCard
            gk={away.goalkeeper}
            cs_prob={predictions.clean_sheet.prob_cs_away}
            teamName={away.info.short}
          />
        </div>
      </div>

      {/* ============ SECTION 6 : MARCHÉS ============ */}
      <div>
        <div className="section-header">
          <span className="section-num">06 /</span>
          <h2>PRÉDICTIONS MARCHÉS</h2>
        </div>

        <window.MarketsGrid predictions={predictions} odds={data.odds} />
      </div>

      {/* ============ SECTION 7 : VALUE BETS ============ */}
      <div>
        <div className="section-header">
          <span className="section-num">07 /</span>
          <h2>💎 VALUE BETS DÉTECTÉS</h2>
          <span className="font-mono text-[10px] text-[var(--accent)] ml-auto">
            {value_bets.length} OPPORTUNITÉS
          </span>
        </div>

        {value_bets.length === 0 ? (
          <div className="card p-8 text-center">
            <div className="font-mono text-[var(--text-muted)] text-sm">
              Aucun value bet détecté pour ce match.<br />
              Les cotes du bookmaker reflètent fidèlement la réalité statistique.
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {value_bets.map((bet, i) => <window.ValueBetCard key={i} bet={bet} />)}
          </div>
        )}
      </div>

      {/* ============ SECTION 8 : H2H ============ */}
      {h2h && h2h.length > 0 && (
        <div>
          <div className="section-header">
            <span className="section-num">08 /</span>
            <h2>HEAD-TO-HEAD (5 DERNIERS)</h2>
          </div>
          <window.H2HTable h2h={h2h} home={home.info} away={away.info} />
        </div>
      )}

    </div>
  );
};

// =============== SOUS-COMPOSANTS ===============

window.TeamScoreCard = function TeamScoreCard({ team, title }) {
  const s = team.scores;
  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <window.TeamLogo team={team.info} size={36} />
          <div>
            <div className="font-display text-xl">{team.info.name}</div>
            <div className="stat-label">{title}</div>
          </div>
        </div>
        <div className="text-right">
          <div className="stat-label">Score global</div>
          <div className="font-display text-3xl text-[var(--accent)]">{s.overall_score.toFixed(0)}</div>
        </div>
      </div>

      <div className="space-y-3 mb-5">
        <window.ScoreMeter value={s.attack_score} label="ATTAQUE" color="var(--red)" />
        <window.ScoreMeter value={s.defense_score} label="DÉFENSE" color="var(--blue)" />
        <window.ScoreMeter value={s.form_score} label="FORME RÉCENTE" color="var(--green)" />
        <window.ScoreMeter value={s.squad_quality} label="QUALITÉ EFFECTIF" color="var(--accent)" />
        <window.ScoreMeter value={s.lineup_stability} label="STABILITÉ XI" color="var(--amber)" />
      </div>

      <div className="grid grid-cols-3 gap-3 pt-5 border-t border-[var(--border)]">
        <div>
          <div className="stat-label">Buts/match</div>
          <div className="font-mono text-base font-semibold mt-1">
            <span className="text-[var(--green)]">{s.goals_for_avg.toFixed(2)}</span>
            <span className="text-[var(--text-muted)] mx-1">/</span>
            <span className="text-[var(--red)]">{s.goals_against_avg.toFixed(2)}</span>
          </div>
        </div>
        <div>
          <div className="stat-label">xG / xGA</div>
          <div className="font-mono text-base font-semibold mt-1">
            {s.xg_avg.toFixed(2)}/{s.xga_avg.toFixed(2)}
          </div>
        </div>
        <div>
          <div className="stat-label">BTTS / O2.5</div>
          <div className="font-mono text-base font-semibold mt-1">
            {s.btts_pct.toFixed(0)}%/{s.over_25_pct.toFixed(0)}%
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 mt-3">
        <div>
          <div className="stat-label">Style de jeu</div>
          <div className="font-mono text-xs mt-1 text-[var(--text-secondary)]">
            {s.play_style.replace(/_/g, " ").toUpperCase()}
          </div>
        </div>
        <div>
          <div className="stat-label">Intensité press</div>
          <div className="font-mono text-xs mt-1 text-[var(--text-secondary)]">
            {(s.press_intensity * 100).toFixed(0)}%
          </div>
        </div>
      </div>
    </div>
  );
};


window.LineupCard = function LineupCard({ team }) {
  const grouped = { GK: [], DEF: [], MID: [], FWD: [] };
  team.starters.forEach(p => {
    if (grouped[p.pos]) grouped[p.pos].push(p);
  });

  return (
    <div className="card p-6">
      <div className="flex items-center gap-3 mb-4">
        <window.TeamLogo team={team.info} size={32} />
        <div className="font-display text-lg">{team.info.name}</div>
        <span className="ml-auto font-mono text-[10px] text-[var(--text-muted)]">
          STAB. {team.scores.lineup_stability.toFixed(0)}%
        </span>
      </div>

      <div className="space-y-3">
        {Object.entries(grouped).map(([pos, players]) => players.length > 0 && (
          <div key={pos}>
            <div className="stat-label mb-2">{pos}</div>
            <div className="space-y-1">
              {players.map(p => (
                <div key={p.id} className="flex items-center gap-2 text-sm">
                  <div className={`pos-badge pos-${p.pos}`}>{p.pos[0]}</div>
                  <span className="flex-1 font-medium">{p.name}</span>
                  <span className="font-mono text-[10px] text-[var(--text-muted)]">
                    {p.starts}/30 titularisations
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};


window.KeyPlayersCard = function KeyPlayersCard({ players, teamName }) {
  return (
    <div className="card p-6">
      <div className="font-display text-xl mb-1">{teamName}</div>
      <div className="stat-label mb-4">PROFILS À FORT IMPACT</div>

      <div className="space-y-3">
        {players.map((p, i) => (
          <div key={p.id} className={`p-4 ${i === 0 ? "bg-[var(--bg-elev)] border border-[var(--accent-dim)]" : "bg-[var(--bg-elev)] border border-[var(--border)]"}`}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className={`pos-badge pos-${p.pos}`}>{p.pos[0]}</div>
                <span className="font-display text-base">{p.name}</span>
                {i === 0 && <span className="tag tag-accent">★ STAR</span>}
              </div>
              <div className="font-mono text-xs text-[var(--text-muted)]">
                {p.minutes}'  ·  {p.starts} titu.
              </div>
            </div>

            <div className="grid grid-cols-4 gap-2 mt-3 text-xs">
              <div className="text-center">
                <div className="stat-label">BUTS</div>
                <div className="font-mono font-semibold mt-1">{p.goals}</div>
              </div>
              <div className="text-center">
                <div className="stat-label">PASSES D.</div>
                <div className="font-mono font-semibold mt-1">{p.assists}</div>
              </div>
              <div className="text-center">
                <div className="stat-label">xG</div>
                <div className="font-mono font-semibold mt-1">{p.xg.toFixed(1)}</div>
              </div>
              <div className="text-center">
                <div className="stat-label">FORME</div>
                <div className="font-mono font-semibold mt-1 text-[var(--accent)]">{p.form_score.toFixed(1)}</div>
              </div>
            </div>

            <div className="mt-3 pt-3 border-t border-[var(--border)] space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-[var(--text-muted)]">Implication offensive</span>
                <span className="font-mono font-semibold">{p.ga_involvement_pct.toFixed(0)}%</span>
              </div>
              <div className="progress">
                <div className="progress-fill" style={{ width: `${Math.min(100, p.ga_involvement_pct * 1.5)}%` }}></div>
              </div>

              <div className="flex justify-between text-xs">
                <span className="text-[var(--text-muted)]">Proba. de marquer</span>
                <span className="font-mono font-semibold text-[var(--green)]">{p.goal_probability.toFixed(0)}%</span>
              </div>
              <div className="progress">
                <div className="progress-fill green" style={{ width: `${p.goal_probability}%` }}></div>
              </div>

              <div className="flex justify-between text-xs">
                <span className="text-[var(--text-muted)]">Proba. de passer</span>
                <span className="font-mono font-semibold text-[var(--blue)]">{p.assist_probability.toFixed(0)}%</span>
              </div>
              <div className="progress">
                <div className="progress-fill blue" style={{ width: `${p.assist_probability}%` }}></div>
              </div>
            </div>

            {p.xg_status.status !== "neutral" && (
              <div className="mt-3 pt-3 border-t border-[var(--border)]">
                <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-widest">
                  <span className={`tag ${p.xg_status.status === "overperforming" ? "tag-amber" : "tag-blue"}`}>
                    {p.xg_status.status === "overperforming" ? "⚠ SURPERFORMANCE xG" : "↑ POTENTIEL DE REBOND"}
                  </span>
                  <span className="text-[var(--text-muted)]">
                    {p.goals} buts / {p.xg.toFixed(1)} xG ({p.xg_status.diff > 0 ? "+" : ""}{p.xg_status.diff.toFixed(1)})
                  </span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};


window.GoalkeeperCard = function GoalkeeperCard({ gk, cs_prob, teamName }) {
  if (!gk || !gk.id) return null;

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="stat-label">{teamName} · GARDIEN</div>
          <div className="font-display text-2xl mt-1">{gk.name}</div>
        </div>
        <div className="text-right">
          <div className="stat-label">Clean sheet att.</div>
          <div className="font-display text-3xl text-[var(--green)]">{cs_prob.toFixed(0)}%</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <div className="stat-label">Arrêts/match</div>
          <div className="font-mono text-lg font-semibold mt-1">{gk.saves_per_game.toFixed(1)}</div>
        </div>
        <div>
          <div className="stat-label">xGOT subi</div>
          <div className="font-mono text-lg font-semibold mt-1">{gk.xgot_faced.toFixed(2)}</div>
        </div>
        <div>
          <div className="stat-label">Clean sheets</div>
          <div className="font-mono text-lg font-semibold mt-1">
            {gk.clean_sheets} ({gk.clean_sheet_rate.toFixed(0)}%)
          </div>
        </div>
        <div>
          <div className="stat-label">Forme</div>
          <div className="font-mono text-lg font-semibold mt-1 text-[var(--accent)]">{gk.form_score.toFixed(1)}/10</div>
        </div>
      </div>

      <div className="pt-4 border-t border-[var(--border)]">
        <window.ScoreMeter value={cs_prob} label="PROBABILITÉ CLEAN SHEET" color="var(--green)" />
      </div>
    </div>
  );
};


window.MarketsGrid = function MarketsGrid({ predictions, odds }) {
  return (
    <div className="grid grid-cols-3 gap-4">
      <window.MarketCard
        title="OVER/UNDER 2.5 BUTS"
        prob1={predictions.over_under_25.prob_over}
        prob2={predictions.over_under_25.prob_under}
        label1="OVER"
        label2="UNDER"
        odds1={odds.over_25}
        odds2={odds.under_25}
        info={`Buts attendus : ${predictions.over_under_25.expected_total.toFixed(2)}`}
      />
      <window.MarketCard
        title="OVER/UNDER 3.5 BUTS"
        prob1={predictions.over_under_35.prob_over}
        prob2={predictions.over_under_35.prob_under}
        label1="OVER"
        label2="UNDER"
        odds1={odds.over_35}
        odds2={odds.under_35}
      />
      <window.MarketCard
        title="BTTS"
        prob1={predictions.btts.prob_yes}
        prob2={predictions.btts.prob_no}
        label1="OUI"
        label2="NON"
        odds1={odds.btts_yes}
        odds2={odds.btts_no}
      />
      <window.MarketCard
        title="CORNERS (LIGNE 9.5)"
        prob1={predictions.corners.prob_over}
        prob2={predictions.corners.prob_under}
        label1="OVER"
        label2="UNDER"
        odds1={odds.corners_over_95}
        odds2={odds.corners_under_95}
        info={`Corners attendus : ${predictions.corners.expected_total.toFixed(1)}`}
      />
      <window.MarketCard
        title="CARTONS J. (LIGNE 4.5)"
        prob1={predictions.cards.prob_over}
        prob2={predictions.cards.prob_under}
        label1="OVER"
        label2="UNDER"
        odds1={odds.cards_over_45}
        odds2={odds.cards_under_45}
        info={`Cartons attendus : ${predictions.cards.expected_total.toFixed(1)} · Intensité ${predictions.intensity_score.toFixed(0)}/100`}
      />
      <window.MarketCard
        title="CLEAN SHEETS"
        prob1={predictions.clean_sheet.prob_cs_home}
        prob2={predictions.clean_sheet.prob_cs_away}
        label1="DOM."
        label2="EXT."
        odds1={odds.cs_home}
        odds2={odds.cs_away}
      />
    </div>
  );
};


window.MarketCard = function MarketCard({ title, prob1, prob2, label1, label2, odds1, odds2, info }) {
  return (
    <div className="card p-5">
      <div className="stat-label mb-3">{title}</div>

      <div className="space-y-3">
        <div>
          <div className="flex justify-between mb-1">
            <span className="font-mono text-xs font-semibold">{label1}</span>
            <div className="flex items-center gap-3">
              <span className="font-mono text-xs text-[var(--text-muted)]">@ {odds1?.toFixed(2)}</span>
              <span className="font-mono text-sm font-semibold">{prob1.toFixed(1)}%</span>
            </div>
          </div>
          <div className="progress">
            <div className="progress-fill green" style={{ width: `${prob1}%` }}></div>
          </div>
        </div>

        <div>
          <div className="flex justify-between mb-1">
            <span className="font-mono text-xs font-semibold">{label2}</span>
            <div className="flex items-center gap-3">
              <span className="font-mono text-xs text-[var(--text-muted)]">@ {odds2?.toFixed(2)}</span>
              <span className="font-mono text-sm font-semibold">{prob2.toFixed(1)}%</span>
            </div>
          </div>
          <div className="progress">
            <div className="progress-fill red" style={{ width: `${prob2}%` }}></div>
          </div>
        </div>
      </div>

      {info && (
        <div className="mt-3 pt-3 border-t border-[var(--border)] font-mono text-[10px] text-[var(--text-muted)] uppercase tracking-widest">
          {info}
        </div>
      )}
    </div>
  );
};


window.ValueBetCard = function ValueBetCard({ bet }) {
  const labels = {
    strong: "🔥 STRONG VALUE",
    high: "✅ HIGH VALUE",
    moderate: "💡 SLIGHT VALUE",
  };

  return (
    <div className={`value-bet ${bet.confidence}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className={`tag ${bet.confidence === "strong" ? "tag-accent" : bet.confidence === "high" ? "tag-green" : "tag-amber"}`}>
            {labels[bet.confidence]}
          </span>
          <span className="font-display text-lg">{bet.market}</span>
        </div>
        <div className="text-right">
          <div className="font-display text-3xl text-[var(--accent)]">+{bet.edge_pct.toFixed(1)}%</div>
          <div className="stat-label">EDGE</div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4 pt-3 border-t border-[var(--border)]">
        <div>
          <div className="stat-label">SÉLECTION</div>
          <div className="font-mono text-sm font-semibold mt-1">{bet.selection}</div>
        </div>
        <div>
          <div className="stat-label">COTE</div>
          <div className="font-mono text-sm font-semibold mt-1">{bet.odds.toFixed(2)}</div>
        </div>
        <div>
          <div className="stat-label">PROBA MODÈLE</div>
          <div className="font-mono text-sm font-semibold mt-1 text-[var(--green)]">{bet.model_prob.toFixed(1)}%</div>
        </div>
        <div>
          <div className="stat-label">PROBA BOOK</div>
          <div className="font-mono text-sm font-semibold mt-1 text-[var(--text-secondary)]">{bet.implied_prob.toFixed(1)}%</div>
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-[var(--border)] text-sm text-[var(--text-secondary)] leading-relaxed">
        {bet.explanation}
      </div>
    </div>
  );
};


window.H2HTable = function H2HTable({ h2h, home, away }) {
  return (
    <div className="card overflow-hidden">
      <table className="data-table">
        <thead>
          <tr>
            <th>DATE</th>
            <th>RENCONTRE</th>
            <th>STADE</th>
            <th className="text-right">SCORE</th>
            <th className="text-right">VAINQUEUR</th>
          </tr>
        </thead>
        <tbody>
          {h2h.map((m, i) => (
            <tr key={i}>
              <td className="text-[var(--text-muted)]">{m.date}</td>
              <td>{home.short} vs {away.short}</td>
              <td className="text-[var(--text-muted)]">{m.venue}</td>
              <td className="text-right font-semibold">{m.score}</td>
              <td className="text-right">
                {m.winner === home.id && <span className="text-[var(--green)]">{home.short}</span>}
                {m.winner === away.id && <span className="text-[var(--red)]">{away.short}</span>}
                {!m.winner && <span className="text-[var(--text-muted)]">NUL</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
