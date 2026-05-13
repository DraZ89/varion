// ========== COMPACT CARD - Look unifie foot/tennis (type screen 2) ==========
// Affiche : logos en background, "Team A vs Team B", competition, timer countdown, nb bets

const { useState: useStateCC, useEffect: useEffectCC } = React;


// Helper : convertit "2026-05-08" + "20:00" en timestamp Unix
function getMatchTimestampMs(dateStr, timeStr) {
  if (!dateStr || !timeStr) return 0;
  // Note : on traite comme heure locale (le frontend l'affichera correctement)
  return new Date(`${dateStr}T${timeStr}:00`).getTime();
}


// Helper : formate un countdown "2J 14h 32m" ou "01:23:45"
function formatCountdown(ms) {
  if (ms <= 0) return "EN COURS";
  const totalSec = Math.floor(ms / 1000);
  const days = Math.floor(totalSec / 86400);
  const hours = Math.floor((totalSec % 86400) / 3600);
  const minutes = Math.floor((totalSec % 3600) / 60);
  const seconds = totalSec % 60;

  if (days > 0) {
    return `${days}J ${hours.toString().padStart(2, "0")}h ${minutes.toString().padStart(2, "0")}m`;
  }
  // Format HH:MM:SS quand <24h
  return `${hours.toString().padStart(2, "0")}:${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
}


// Hook : countdown qui se rafraichit chaque seconde
function useCountdown(targetMs) {
  const [now, setNow] = useStateCC(Date.now());
  useEffectCC(() => {
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, []);
  return targetMs - now;
}


// ========== CARD UNIFIEE (foot + tennis) ==========
window.CompactCard = function CompactCard({ match, sport, onClick }) {
  const isTennis = sport === "tennis";

  // Recuperer les infos selon le sport
  let homeName, awayName, homeColor, awayColor, homeShort, awayShort;
  let competition, dateStr, timeStr, betsCount;

  if (isTennis) {
    homeName = match.player_a?.name || match.home || "?";
    awayName = match.player_b?.name || match.away || "?";
    homeShort = (match.player_a?.country_code || homeName.slice(0, 3)).toUpperCase();
    awayShort = (match.player_b?.country_code || awayName.slice(0, 3)).toUpperCase();
    homeColor = match.tour === "WTA" ? "#d946ef" : "#3b82f6";  // magenta WTA, bleu ATP
    awayColor = match.tour === "WTA" ? "#a855f7" : "#1e40af";
    competition = `${match.tour || "ATP"} · ${match.tournament || ""}`;
    dateStr = match.date;
    timeStr = match.time;
    betsCount = (match.value_bets || []).length;
  } else {
    homeName = match.home?.name || match.home || "?";
    awayName = match.away?.name || match.away || "?";
    homeShort = match.home?.short || homeName.slice(0, 3).toUpperCase();
    awayShort = match.away?.short || awayName.slice(0, 3).toUpperCase();
    homeColor = match.home?.logo_color || "#dc2626";
    awayColor = match.away?.logo_color || "#1e40af";
    competition = match.competition || "Football";
    dateStr = match.date;
    timeStr = match.kickoff;
    betsCount = match.value_bets_count || 0;
  }

  // Logos URLs : on prend match.home/away.logo_url s'il y a, sinon fallback color
  const homeLogo = isTennis ? null : match.home?.logo_url;
  const awayLogo = isTennis ? null : match.away?.logo_url;

  // Countdown
  const targetMs = getMatchTimestampMs(dateStr, timeStr);
  const timeLeft = useCountdown(targetMs);
  const countdownStr = formatCountdown(timeLeft);

  return (
    <div
      className={`compact-card ${onClick ? "cursor-pointer" : ""}`}
      onClick={onClick}
    >
      {/* Background avec gradient des couleurs des equipes */}
      <div
        className="compact-card-bg"
        style={{
          background: `linear-gradient(105deg, ${homeColor}33 0%, ${homeColor}55 35%, ${awayColor}55 65%, ${awayColor}33 100%)`,
        }}
      >
        {/* Logos / initiales en grand au centre */}
        <div className="compact-card-logos">
          <div className="compact-logo compact-logo-home">
            {homeLogo ? (
              <img src={homeLogo} alt={homeShort} />
            ) : (
              <div className="compact-logo-fallback" style={{ background: homeColor }}>
                {homeShort}
              </div>
            )}
          </div>

          <div className="compact-vs-icon">
            {isTennis ? "🎾" : "⚽"}
          </div>

          <div className="compact-logo compact-logo-away">
            {awayLogo ? (
              <img src={awayLogo} alt={awayShort} />
            ) : (
              <div className="compact-logo-fallback" style={{ background: awayColor }}>
                {awayShort}
              </div>
            )}
          </div>
        </div>

        {/* Badge nombre de paris en haut a droite */}
        {betsCount > 0 && (
          <div className="compact-bets-badge">
            <span className="compact-bets-num">{betsCount}</span>
            <span className="compact-bets-label">{betsCount > 1 ? "PARIS" : "PARI"}</span>
          </div>
        )}

        {/* Tag sport en haut a gauche */}
        <div className="compact-sport-tag">
          {isTennis ? (match.tour || "ATP") : "FOOT"}
        </div>
      </div>

      {/* Info en bas : titre + competition + countdown */}
      <div className="compact-card-info">
        <div className="compact-card-title">
          {homeShort} <span className="compact-vs">vs</span> {awayShort}
        </div>
        <div className="compact-card-meta">
          <span className="compact-card-competition">{competition}</span>
          <span className="compact-card-countdown">{countdownStr}</span>
        </div>
      </div>
    </div>
  );
};
