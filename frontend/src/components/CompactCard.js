// ========== COMPACT CARD - Look unifie foot/tennis (type screen 2) ==========
// Affiche : logos en background, "Team A vs Team B", competition, timer countdown, nb bets

const { useState: useStateCC, useEffect: useEffectCC } = React;


// Helper : icone surface tennis (dot coloré, pas d'emoji)
function getSurfaceIcon(surface) {
  const s = (surface || "").toLowerCase();
  if (s.includes("clay")) return { dot: "#E8743F", label: "CLAY", color: "#E8743F" };
  if (s.includes("grass")) return { dot: "#73F5A1", label: "GRASS", color: "#73F5A1" };
  if (s.includes("indoor") || s.includes("carpet")) return { dot: "#A78BFA", label: "INDOOR", color: "#A78BFA" };
  return { dot: "#5B9DFF", label: "HARD", color: "#5B9DFF" };
}


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
  const [, forceCCUpdate] = React.useState({});
  React.useEffect(() => {
    const h = () => forceCCUpdate({});
    window.addEventListener("varion-lang-change", h);
    return () => window.removeEventListener("varion-lang-change", h);
  }, []);
  const isTennis = sport === "tennis";

  // Recuperer les infos selon le sport
  let homeName, awayName, homeColor, awayColor, homeShort, awayShort;
  let competition, dateStr, timeStr, betsCount;

  if (isTennis) {
    const pa = match.player_a || {};
    const pb = match.player_b || {};
    homeName = pa.name || "?";
    awayName = pb.name || "?";
    // On utilise le code pays (3 lettres) si dispo, sinon les 3 premieres lettres du nom
    const paCountry = pa.country || "";
    const pbCountry = pb.country || "";
    homeShort = (paCountry || homeName.slice(0, 3)).toUpperCase();
    awayShort = (pbCountry || awayName.slice(0, 3)).toUpperCase();
    homeColor = match.tour === "WTA" ? "#d946ef" : "#3b82f6";
    awayColor = match.tour === "WTA" ? "#a855f7" : "#1e40af";
    competition = `${match.tour || "ATP"}${match.tournament ? " · " + match.tournament : ""}`;
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

  // Donnees specifiques tennis
  const tennisData = isTennis ? {
    pa: match.player_a || {},
    pb: match.player_b || {},
    paRank: match.player_a?.rank,
    pbRank: match.player_b?.rank,
    surface: getSurfaceIcon(match.surface),
  } : null;

  // Pour le titre tennis : nom court "Basilashvili" (dernier mot)
  const getLastName = (fullName) => {
    if (!fullName) return "";
    const parts = fullName.trim().split(" ");
    return parts[parts.length - 1];
  };
  const homeTitle = isTennis ? getLastName(homeName) : homeShort;
  const awayTitle = isTennis ? getLastName(awayName) : awayShort;

  // Countdown : on utilise start_timestamp_ms si dispo (UTC, fiable),
  // sinon fallback sur date+time interprete comme heure locale
  let targetMs;
  if (match.start_timestamp_ms && match.start_timestamp_ms > 0) {
    targetMs = match.start_timestamp_ms;
  } else if (match.startTimestamp && match.startTimestamp > 0) {
    // Foot SportAPI7 : startTimestamp est en SECONDES Unix
    targetMs = match.startTimestamp * 1000;
  } else {
    targetMs = getMatchTimestampMs(dateStr, timeStr);
  }
  const timeLeft = useCountdown(targetMs);
  const countdownStr = formatCountdown(timeLeft);

  // Pour le tennis : on n'a pas l'heure exacte (limitation Matchstat),
  // on affiche juste la date format court "06 mai" + disclaimer
  // Pour le foot : on a le timestamp precis, on affiche heure locale + countdown
  let displayTime;
  if (isTennis) {
    if (targetMs > 0) {
      const dt = new Date(targetMs);
      const dateFormatted = dt.toLocaleDateString(undefined, {
        day: "2-digit",
        month: "short",
      });
      displayTime = { primary: `${dateFormatted}`, secondary: "Horaire confirme avant le match" };
    } else {
      displayTime = { primary: dateStr, secondary: "" };
    }
  } else {
    // Foot : heure precise + countdown
    const matchLocalTime = targetMs > 0
      ? new Date(targetMs).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })
      : "";
    displayTime = {
      primary: matchLocalTime || "",
      secondary: countdownStr,
    };
  }

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
            ) : isTennis && tennisData.pa.country ? (
              <div className="compact-logo-flag" style={{ background: homeColor }}>
                <window.Flag country={tennisData.pa.country} width={36} height={24}/>
                <span className="compact-flag-code">{homeShort}</span>
              </div>
            ) : (
              <div className="compact-logo-fallback" style={{ background: homeColor }}>
                {homeShort}
              </div>
            )}
          </div>

          <div className="compact-vs-icon">VS</div>

          <div className="compact-logo compact-logo-away">
            {awayLogo ? (
              <img src={awayLogo} alt={awayShort} />
            ) : isTennis && tennisData.pb.country ? (
              <div className="compact-logo-flag" style={{ background: awayColor }}>
                <window.Flag country={tennisData.pb.country} width={36} height={24}/>
                <span className="compact-flag-code">{awayShort}</span>
              </div>
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

        {/* Tennis : badge surface en bas a gauche */}
        {isTennis && (
          <div
            className="compact-surface-badge"
            style={{ borderColor: tennisData.surface.color }}
          >
            <span style={{
              display: "inline-block", width: 8, height: 8, borderRadius: "50%",
              background: tennisData.surface.dot,
              boxShadow: `0 0 6px ${tennisData.surface.dot}`,
            }}/>
            {window.tApi ? window.tApi(tennisData.surface.label.toLowerCase()).toUpperCase() : tennisData.surface.label}
          </div>
        )}
      </div>

      {/* Info en bas : titre + competition + countdown */}
      <div className="compact-card-info">
        <div className="compact-card-title">
          {homeTitle}
          {isTennis && tennisData.paRank && (
            <span className="compact-rank">#{tennisData.paRank}</span>
          )}
          <span className="compact-vs">vs</span>
          {awayTitle}
          {isTennis && tennisData.pbRank && (
            <span className="compact-rank">#{tennisData.pbRank}</span>
          )}
        </div>
        <div className="compact-card-meta">
          <span className="compact-card-competition">{competition}</span>
          <div className="flex flex-col items-end">
            {displayTime.primary && (
              <span className="compact-card-localtime">{displayTime.primary}</span>
            )}
            {displayTime.secondary && (
              <span className="compact-card-countdown">{displayTime.secondary}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
