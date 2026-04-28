// Match Card - utilisé dans le dashboard

window.MatchCard = function MatchCard({ match, onClick }) {
  const { home, away, predictions_summary: pred, top_value_bet, confidence_score, value_bets_count } = match;
  const conf = window.helpers.confidenceLabel(confidence_score);

  return (
    <div className="card card-hover match-card p-5 fade-in" onClick={onClick}>
      {/* Top row : meta */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] uppercase tracking-widest text-[var(--text-muted)]">
            {match.competition}
          </span>
          {match.is_derby && <span className="tag tag-amber">DERBY</span>}
          {match.stakes === "high" && <span className="tag tag-red">ENJEU FORT</span>}
        </div>
        <span className="font-mono text-xs text-[var(--text-muted)]">
          {window.helpers.formatDate(match.date)} · {match.kickoff}
        </span>
      </div>

      {/* Teams + odds main */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3 flex-1">
          <window.TeamLogo team={home} size={48} />
          <div>
            <div className="font-display text-xl">{home.name}</div>
            <div className="font-mono text-[10px] text-[var(--text-muted)]">#{home.rank} · {match.venue}</div>
          </div>
        </div>

        <div className="text-center px-4">
          <div className="font-mono text-[10px] text-[var(--text-muted)] uppercase tracking-widest">VS</div>
        </div>

        <div className="flex items-center gap-3 flex-1 justify-end">
          <div className="text-right">
            <div className="font-display text-xl">{away.name}</div>
            <div className="font-mono text-[10px] text-[var(--text-muted)]">#{away.rank} · Extérieur</div>
          </div>
          <window.TeamLogo team={away} size={48} />
        </div>
      </div>

      {/* Proba gauge */}
      <div className="mb-4">
        <window.ProbaGauge
          home={pred.prob_home}
          draw={pred.prob_draw}
          away={pred.prob_away}
          homeLabel={home.short}
          awayLabel={away.short}
        />
      </div>

      {/* Indicators row */}
      <div className="grid grid-cols-4 gap-3 pt-4 border-t border-[var(--border)]">
        <div>
          <div className="stat-label">Buts att.</div>
          <div className="font-mono text-base font-semibold mt-1">{pred.expected_goals.toFixed(2)}</div>
        </div>
        <div>
          <div className="stat-label">Corners att.</div>
          <div className="font-mono text-base font-semibold mt-1">{pred.expected_corners.toFixed(1)}</div>
        </div>
        <div>
          <div className="stat-label">Cartons att.</div>
          <div className="font-mono text-base font-semibold mt-1">{pred.expected_cards.toFixed(1)}</div>
        </div>
        <div>
          <div className="stat-label">Score prob.</div>
          <div className="font-mono text-base font-semibold mt-1">{pred.most_likely_score}</div>
        </div>
      </div>

      {/* Value bet flag + confidence */}
      <div className="flex items-center justify-between mt-4 pt-4 border-t border-[var(--border)]">
        <div className="flex items-center gap-3">
          {top_value_bet ? (
            <>
              <span className="tag tag-accent">
                {value_bets_count} VALUE {value_bets_count > 1 ? "BETS" : "BET"}
              </span>
              <span className="font-mono text-xs text-[var(--text-secondary)]">
                Top: <span className="text-[var(--accent)] font-semibold">{top_value_bet.market}</span>
                {" "}@ <span className="text-white">{top_value_bet.odds.toFixed(2)}</span>
                {" "}<span className="text-[var(--green)]">+{top_value_bet.edge_pct.toFixed(1)}%</span>
              </span>
            </>
          ) : (
            <span className="font-mono text-[10px] text-[var(--text-muted)] uppercase tracking-widest">
              · Pas de value
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] uppercase tracking-widest" style={{ color: conf.color }}>
            CONF. {confidence_score}/100
          </span>
          <span className="text-[var(--text-muted)]">→</span>
        </div>
      </div>
    </div>
  );
};
