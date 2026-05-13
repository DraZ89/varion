// ========== I18N SYSTEM ==========
// Traduction UI complete : FR / EN / ES

window.I18N_DICTIONARIES = {
  fr: {
    // Header
    "app.subtitle": "Sports betting analytics",
    "nav.home": "Accueil",
    "nav.football": "Foot",
    "nav.tennis": "Tennis",
    "nav.value": "Value Bets",

    // Home
    "home.matchesCount": "matchs",
    "home.football": "Football",
    "home.tennis": "Tennis",
    "home.valueBets": "Value Bets",
    "home.sort": "Tri",
    "home.chronological": "Chronologique",
    "home.filter": "Filtre",
    "home.all": "Tous",
    "home.today": "Aujourd'hui",
    "home.tomorrow": "Demain",
    "home.later": "Plus tard",
    "home.noMatches": "Aucun match disponible",
    "home.foot": "Foot",

    // Match general
    "match.bet": "PARI",
    "match.bets": "PARIS",
    "match.live": "LIVE",
    "match.scheduled": "Programme",
    "match.timeIndicative": "Horaire exact confirme par le bookmaker quelques heures avant le match",
    "match.back": "Retour",

    // Tabs detail
    "tab.overview": "Vue d'ensemble",
    "tab.stats": "Stats",
    "tab.h2h": "H2H",

    // Verdict / AI
    "ai.varionAi": "Varion AI",
    "ai.completeAnalysis": "Analyse complete · mise a jour il y a peu",
    "ai.predictionWinner": "Prediction vainqueur",
    "ai.bookmakerOdds": "Cotes bookmaker",
    "ai.bookmakerOddsEstimated": "Cotes estimees (modele)",
    "ai.totalGamesPredicted": "Total games prevu",
    "ai.headToHead": "Face-a-face",
    "ai.matches": "matchs",
    "ai.match": "match",
    "ai.valueBets": "Paris a valeur",
    "ai.modelPicks": "Predictions IA",
    "ai.oddsUnavailable": "Cote indisponible chez les bookmakers",
    "ai.notAvailable": "INDISPO",
    "ai.estimated": "EST.",
    "ai.modelPick": "Pick IA",
    "ai.modelPickDesc": "Prediction du modele (sans cote bookmaker)",
    "ai.valueBetDetected": "value bet detecte",
    "ai.valueBetsDetected": "value bets detectes",
    "ai.mostProbableScore": "Score le plus probable",
    "ai.expectedSets": "Sets attendus",

    // Profil
    "profile.title": "Profil",
    "profile.height": "cm",
    "profile.weight": "kg",
    "profile.lefty": "Gaucher",
    "profile.righty": "Droitier",
    "profile.twoHandedBackhand": "(revers 2 mains)",
    "profile.oneHandedBackhand": "(revers 1 main)",
    "profile.proSince": "Pro depuis",
    "profile.bornIn": "Ne a",
    "profile.formRecent": "Forme recente",
    "profile.eloGlobal": "ELO Global",
    "profile.unranked": "Hors classement",
    "profile.atp": "ATP",
    "profile.wta": "WTA",

    // Career stats
    "career.title": "Comparaison carriere",
    "career.service": "Service",
    "career.returnBreak": "Retour & Break",
    "career.mentalClutch": "Mental & Clutch",
    "career.firstServes": "1ers serv",
    "career.ptsFirstServe": "Pts/1er",
    "career.ptsSecondServe": "Pts/2nd",
    "career.acesPerMatch": "Aces/m",
    "career.returnPts": "Pts retour",
    "career.breakPct": "% break",
    "career.win1stSet": "Win 1er set",
    "career.comeback": "Remontada",
    "career.decidingSet": "Set decisif",
    "career.tiebreak": "Tiebreak",
    "career.titles": "titres",
    "career.title_one": "titre",

    // Perf breakdown
    "perf.title": "Bilan recent",
    "perf.yearsAnalyzed": "Annees analysees",
    "perf.bySurface": "Par surface",
    "perf.vsLevel": "Vs niveau adv",
    "perf.hard": "Hard",
    "perf.clay": "Clay",
    "perf.grass": "Grass",
    "perf.indoor": "Indoor",
    "perf.vsTop10": "vs Top 10",
    "perf.vsTop20": "vs Top 20",
    "perf.vsTop50": "vs Top 50",
    "perf.vsTop100": "vs Top 100",

    // H2H
    "h2h.detailedTitle": "H2H detaille",
    "h2h.smallSample": "Echantillon faible : interpretations a relativiser",
    "h2h.bySurface": "H2H par surface",
    "h2h.never": "jamais",
    "h2h.perfInDuels": "Perf dans leurs duels",
    "h2h.firstServes": "1ers serv",
    "h2h.decidingSet": "Set decis",
    "h2h.tiebreak": "Tiebreak",
    "h2h.avgDuration": "Duree moyenne",
    "h2h.last5": "5 derniers face-a-face",
    "h2h.empty": "Aucun face-a-face precedent enregistre.",

    // Months (court)
    "month.short.0": "janv", "month.short.1": "fev", "month.short.2": "mars",
    "month.short.3": "avr", "month.short.4": "mai", "month.short.5": "juin",
    "month.short.6": "juil", "month.short.7": "aout", "month.short.8": "sept",
    "month.short.9": "oct", "month.short.10": "nov", "month.short.11": "dec",

    // AI Stats page
    "nav.aiStats": "Performance IA",
    "aistats.title": "Performance IA Varion",
    "aistats.subtitle": "Suivi de la fiabilite de nos predictions sur les paris a valeur",
    "aistats.loading": "Chargement des stats...",
    "aistats.empty.title": "Aucun pari encore resolu",
    "aistats.empty.desc": "Les premiers paris IA seront affiches ici une fois les matchs joues. Reviens dans quelques jours pour voir nos performances en temps reel.",
    "aistats.globalScore": "Score global de l'IA",
    "aistats.basedOn": "Base sur",
    "aistats.settledBets": "paris resolus",
    "aistats.winRate": "Win rate",
    "aistats.avgEdge": "Edge moyen",
    "aistats.modelVsBookies": "modele vs cotes",
    "aistats.totalBets": "Total paris",
    "aistats.pending": "en attente",
    "aistats.target": "Objectif",
    "aistats.aboveTarget": "Au-dessus de l'objectif 90%",
    "aistats.pointsBelowTarget": "points sous l'objectif 90%",
    "aistats.elite": "Au-dessus de l'objectif",
    "aistats.solid": "Performance solide",
    "aistats.average": "Performance moyenne",
    "aistats.toReview": "A surveiller",
    "aistats.bySurface": "Par surface",
    "aistats.byTour": "Par tour",
    "aistats.byConfidence": "Par confiance modele",
    "aistats.bySport": "Par sport",
    "aistats.confidence": "Confiance",
    "aistats.recentHistory": "Historique recent",
    "aistats.edge": "edge",
    "aistats.cta.label": "Varion Pro",
    "aistats.cta.title": "Acces complet aux predictions IA",
    "aistats.cta.descGood": "Notre IA affiche un track record solide. Souscrivez pour acceder a tous les value bets en temps reel, l'historique complet, et les alertes mobile.",
    "aistats.cta.descNeutral": "Suivez les performances de notre IA, recevez les value bets en temps reel et l'historique complet en souscrivant a Varion Pro.",
    "aistats.cta.winRate": "Win rate IA",
    "aistats.cta.roi": "ROI moyen",
    "aistats.cta.edge": "Edge moyen",
    "aistats.cta.button": "Souscrire a Varion Pro",
    "aistats.cta.disclaimer": "Pariez de maniere responsable. 18+. La performance passee ne garantit pas les resultats futurs.",

    "aistats.import.title": "Importer un fichier de suivi",
    "aistats.import.desc": "Glisse ton fichier suivi_varion.xlsx pour mettre a jour les stats. Les paris existants sont mis a jour, les nouveaux ajoutes.",
    "aistats.import.cta": "Glisse ton .xlsx ici ou clique pour selectionner",
    "aistats.import.drop": "Relache le fichier ici",
    "aistats.import.loading": "Lecture du fichier en cours...",
    "aistats.import.success": "paris importes avec succes",
    "aistats.import.errFormat": "Format invalide : seuls .xlsx et .xls sont acceptes",
    "aistats.import.errEmpty": "Aucun pari trouve dans le fichier",
    "aistats.import.errParse": "Erreur de lecture",
    "aistats.importedStats": "Stats depuis fichier importe",
    "aistats.clearImport": "Effacer l'import",
    "aistats.importedPrincipales": "Predictions principales",
    "aistats.importedRecommandees": "Paris recommandes",
    "aistats.winRateWinner": "Win rate vainqueur",
    "aistats.scoreExact": "% Score exact",
    "aistats.gamesOver": "% Jeux Over",
  },

  en: {
    "app.subtitle": "Sports betting analytics",
    "nav.home": "Home",
    "nav.football": "Football",
    "nav.tennis": "Tennis",
    "nav.value": "Value Bets",

    "home.matchesCount": "matches",
    "home.football": "Football",
    "home.tennis": "Tennis",
    "home.valueBets": "Value Bets",
    "home.sort": "Sort",
    "home.chronological": "Chronological",
    "home.filter": "Filter",
    "home.all": "All",
    "home.today": "Today",
    "home.tomorrow": "Tomorrow",
    "home.later": "Later",
    "home.noMatches": "No matches available",
    "home.foot": "Football",

    "match.bet": "BET",
    "match.bets": "BETS",
    "match.live": "LIVE",
    "match.scheduled": "Scheduled",
    "match.timeIndicative": "Exact time confirmed by bookmaker a few hours before the match",
    "match.back": "Back",

    "tab.overview": "Overview",
    "tab.stats": "Stats",
    "tab.h2h": "H2H",

    "ai.varionAi": "Varion AI",
    "ai.completeAnalysis": "Full analysis · recently updated",
    "ai.predictionWinner": "Winner prediction",
    "ai.bookmakerOdds": "Bookmaker odds",
    "ai.bookmakerOddsEstimated": "Estimated odds (model)",
    "ai.totalGamesPredicted": "Expected total games",
    "ai.headToHead": "Head-to-head",
    "ai.matches": "matches",
    "ai.match": "match",
    "ai.valueBets": "Value bets",
    "ai.modelPicks": "AI Predictions",
    "ai.oddsUnavailable": "No odds available at bookmakers",
    "ai.notAvailable": "N/A",
    "ai.estimated": "EST.",
    "ai.modelPick": "AI Pick",
    "ai.modelPickDesc": "Model prediction (no bookmaker odds)",
    "ai.valueBetDetected": "value bet detected",
    "ai.valueBetsDetected": "value bets detected",
    "ai.mostProbableScore": "Most probable score",
    "ai.expectedSets": "Expected sets",

    "profile.title": "Profile",
    "profile.height": "cm",
    "profile.weight": "kg",
    "profile.lefty": "Left-handed",
    "profile.righty": "Right-handed",
    "profile.twoHandedBackhand": "(two-handed backhand)",
    "profile.oneHandedBackhand": "(one-handed backhand)",
    "profile.proSince": "Pro since",
    "profile.bornIn": "Born in",
    "profile.formRecent": "Recent form",
    "profile.eloGlobal": "Global ELO",
    "profile.unranked": "Unranked",
    "profile.atp": "ATP",
    "profile.wta": "WTA",

    "career.title": "Career comparison",
    "career.service": "Serve",
    "career.returnBreak": "Return & Break",
    "career.mentalClutch": "Mental & Clutch",
    "career.firstServes": "1st serve",
    "career.ptsFirstServe": "Pts/1st",
    "career.ptsSecondServe": "Pts/2nd",
    "career.acesPerMatch": "Aces/m",
    "career.returnPts": "Return pts",
    "career.breakPct": "% break",
    "career.win1stSet": "Win 1st set",
    "career.comeback": "Comeback",
    "career.decidingSet": "Deciding set",
    "career.tiebreak": "Tiebreak",
    "career.titles": "titles",
    "career.title_one": "title",

    "perf.title": "Recent record",
    "perf.yearsAnalyzed": "Years analyzed",
    "perf.bySurface": "By surface",
    "perf.vsLevel": "Vs opp. ranking",
    "perf.hard": "Hard",
    "perf.clay": "Clay",
    "perf.grass": "Grass",
    "perf.indoor": "Indoor",
    "perf.vsTop10": "vs Top 10",
    "perf.vsTop20": "vs Top 20",
    "perf.vsTop50": "vs Top 50",
    "perf.vsTop100": "vs Top 100",

    "h2h.detailedTitle": "Detailed H2H",
    "h2h.smallSample": "Small sample: interpret with caution",
    "h2h.bySurface": "H2H by surface",
    "h2h.never": "never",
    "h2h.perfInDuels": "Perf in their duels",
    "h2h.firstServes": "1st serve",
    "h2h.decidingSet": "Deciding set",
    "h2h.tiebreak": "Tiebreak",
    "h2h.avgDuration": "Avg duration",
    "h2h.last5": "Last 5 head-to-heads",
    "h2h.empty": "No prior head-to-head recorded.",

    "month.short.0": "Jan", "month.short.1": "Feb", "month.short.2": "Mar",
    "month.short.3": "Apr", "month.short.4": "May", "month.short.5": "Jun",
    "month.short.6": "Jul", "month.short.7": "Aug", "month.short.8": "Sep",
    "month.short.9": "Oct", "month.short.10": "Nov", "month.short.11": "Dec",

    // AI Stats page
    "nav.aiStats": "AI Performance",
    "aistats.title": "Varion AI Performance",
    "aistats.subtitle": "Tracking the reliability of our predictions on value bets",
    "aistats.loading": "Loading stats...",
    "aistats.empty.title": "No bets settled yet",
    "aistats.empty.desc": "The first AI bets will appear here once matches are played. Come back in a few days to see real-time performance.",
    "aistats.globalScore": "Global AI score",
    "aistats.basedOn": "Based on",
    "aistats.settledBets": "settled bets",
    "aistats.winRate": "Win rate",
    "aistats.avgEdge": "Avg edge",
    "aistats.modelVsBookies": "model vs odds",
    "aistats.totalBets": "Total bets",
    "aistats.pending": "pending",
    "aistats.target": "Target",
    "aistats.aboveTarget": "Above 90% target",
    "aistats.pointsBelowTarget": "points below 90% target",
    "aistats.elite": "Above target",
    "aistats.solid": "Solid performance",
    "aistats.average": "Average performance",
    "aistats.toReview": "Needs review",
    "aistats.bySurface": "By surface",
    "aistats.byTour": "By tour",
    "aistats.byConfidence": "By model confidence",
    "aistats.bySport": "By sport",
    "aistats.confidence": "Confidence",
    "aistats.recentHistory": "Recent history",
    "aistats.edge": "edge",
    "aistats.cta.label": "Varion Pro",
    "aistats.cta.title": "Full access to AI predictions",
    "aistats.cta.descGood": "Our AI shows a solid track record. Subscribe for real-time value bets, full history, and mobile alerts.",
    "aistats.cta.descNeutral": "Follow our AI's performance, get real-time value bets and full history with Varion Pro.",
    "aistats.cta.winRate": "AI Win rate",
    "aistats.cta.roi": "Avg ROI",
    "aistats.cta.edge": "Avg edge",
    "aistats.cta.button": "Subscribe to Varion Pro",
    "aistats.cta.disclaimer": "Gamble responsibly. 18+. Past performance does not guarantee future results.",

    "aistats.import.title": "Import tracking file",
    "aistats.import.desc": "Drop your suivi_varion.xlsx file to update stats. Existing bets are updated, new ones added.",
    "aistats.import.cta": "Drop your .xlsx here or click to select",
    "aistats.import.drop": "Release file here",
    "aistats.import.loading": "Reading file...",
    "aistats.import.success": "bets imported successfully",
    "aistats.import.errFormat": "Invalid format: only .xlsx and .xls are accepted",
    "aistats.import.errEmpty": "No bet found in file",
    "aistats.import.errParse": "Read error",
    "aistats.importedStats": "Stats from imported file",
    "aistats.clearImport": "Clear import",
    "aistats.importedPrincipales": "Main predictions",
    "aistats.importedRecommandees": "Recommended bets",
    "aistats.winRateWinner": "Winner win rate",
    "aistats.scoreExact": "% Exact score",
    "aistats.gamesOver": "% Games Over",
  },

  es: {
    "app.subtitle": "Analitica de apuestas deportivas",
    "nav.home": "Inicio",
    "nav.football": "Futbol",
    "nav.tennis": "Tenis",
    "nav.value": "Value Bets",

    "home.matchesCount": "partidos",
    "home.football": "Futbol",
    "home.tennis": "Tenis",
    "home.valueBets": "Value Bets",
    "home.sort": "Orden",
    "home.chronological": "Cronologico",
    "home.filter": "Filtro",
    "home.all": "Todos",
    "home.today": "Hoy",
    "home.tomorrow": "Manana",
    "home.later": "Mas tarde",
    "home.noMatches": "Sin partidos disponibles",
    "home.foot": "Futbol",

    "match.bet": "APUESTA",
    "match.bets": "APUESTAS",
    "match.live": "EN VIVO",
    "match.scheduled": "Programado",
    "match.timeIndicative": "Hora exacta confirmada por el bookmaker unas horas antes del partido",
    "match.back": "Volver",

    "tab.overview": "Resumen",
    "tab.stats": "Estadisticas",
    "tab.h2h": "H2H",

    "ai.varionAi": "Varion AI",
    "ai.completeAnalysis": "Analisis completo · actualizado hace poco",
    "ai.predictionWinner": "Prediccion ganador",
    "ai.bookmakerOdds": "Cuotas bookmaker",
    "ai.bookmakerOddsEstimated": "Cuotas estimadas (modelo)",
    "ai.totalGamesPredicted": "Total juegos previstos",
    "ai.headToHead": "Cara a cara",
    "ai.matches": "partidos",
    "ai.match": "partido",
    "ai.valueBets": "Apuestas de valor",
    "ai.modelPicks": "Predicciones IA",
    "ai.oddsUnavailable": "Cuota no disponible en los corredores",
    "ai.notAvailable": "N/D",
    "ai.estimated": "EST.",
    "ai.modelPick": "Pick IA",
    "ai.modelPickDesc": "Prediccion del modelo (sin cuotas bookmaker)",
    "ai.valueBetDetected": "value bet detectado",
    "ai.valueBetsDetected": "value bets detectados",
    "ai.mostProbableScore": "Marcador mas probable",
    "ai.expectedSets": "Sets esperados",

    "profile.title": "Perfil",
    "profile.height": "cm",
    "profile.weight": "kg",
    "profile.lefty": "Zurdo",
    "profile.righty": "Diestro",
    "profile.twoHandedBackhand": "(reves a dos manos)",
    "profile.oneHandedBackhand": "(reves a una mano)",
    "profile.proSince": "Pro desde",
    "profile.bornIn": "Nacido en",
    "profile.formRecent": "Forma reciente",
    "profile.eloGlobal": "ELO Global",
    "profile.unranked": "Sin clasificacion",
    "profile.atp": "ATP",
    "profile.wta": "WTA",

    "career.title": "Comparacion carrera",
    "career.service": "Saque",
    "career.returnBreak": "Resto & Break",
    "career.mentalClutch": "Mental & Clutch",
    "career.firstServes": "1er saque",
    "career.ptsFirstServe": "Pts/1er",
    "career.ptsSecondServe": "Pts/2do",
    "career.acesPerMatch": "Aces/p",
    "career.returnPts": "Pts resto",
    "career.breakPct": "% break",
    "career.win1stSet": "Gana 1er set",
    "career.comeback": "Remontada",
    "career.decidingSet": "Set decisivo",
    "career.tiebreak": "Tiebreak",
    "career.titles": "titulos",
    "career.title_one": "titulo",

    "perf.title": "Balance reciente",
    "perf.yearsAnalyzed": "Anos analizados",
    "perf.bySurface": "Por superficie",
    "perf.vsLevel": "Vs nivel rival",
    "perf.hard": "Dura",
    "perf.clay": "Tierra",
    "perf.grass": "Hierba",
    "perf.indoor": "Indoor",
    "perf.vsTop10": "vs Top 10",
    "perf.vsTop20": "vs Top 20",
    "perf.vsTop50": "vs Top 50",
    "perf.vsTop100": "vs Top 100",

    "h2h.detailedTitle": "H2H detallado",
    "h2h.smallSample": "Muestra pequena: interpretar con cautela",
    "h2h.bySurface": "H2H por superficie",
    "h2h.never": "nunca",
    "h2h.perfInDuels": "Perf en sus duelos",
    "h2h.firstServes": "1er saque",
    "h2h.decidingSet": "Set decis",
    "h2h.tiebreak": "Tiebreak",
    "h2h.avgDuration": "Duracion media",
    "h2h.last5": "5 ultimos cara a cara",
    "h2h.empty": "Sin enfrentamientos previos registrados.",

    "month.short.0": "ene", "month.short.1": "feb", "month.short.2": "mar",
    "month.short.3": "abr", "month.short.4": "may", "month.short.5": "jun",
    "month.short.6": "jul", "month.short.7": "ago", "month.short.8": "sep",
    "month.short.9": "oct", "month.short.10": "nov", "month.short.11": "dic",

    // AI Stats page
    "nav.aiStats": "Rendimiento IA",
    "aistats.title": "Rendimiento IA Varion",
    "aistats.subtitle": "Seguimiento de la fiabilidad de nuestras predicciones en value bets",
    "aistats.loading": "Cargando estadisticas...",
    "aistats.empty.title": "Sin apuestas resueltas todavia",
    "aistats.empty.desc": "Las primeras apuestas IA se mostraran aqui una vez se hayan jugado los partidos. Vuelve en unos dias para ver el rendimiento en tiempo real.",
    "aistats.globalScore": "Puntuacion global IA",
    "aistats.basedOn": "Basado en",
    "aistats.settledBets": "apuestas resueltas",
    "aistats.winRate": "Tasa acierto",
    "aistats.avgEdge": "Edge medio",
    "aistats.modelVsBookies": "modelo vs cuotas",
    "aistats.totalBets": "Total apuestas",
    "aistats.pending": "pendientes",
    "aistats.target": "Objetivo",
    "aistats.aboveTarget": "Por encima del objetivo 90%",
    "aistats.pointsBelowTarget": "puntos bajo el objetivo 90%",
    "aistats.elite": "Por encima del objetivo",
    "aistats.solid": "Rendimiento solido",
    "aistats.average": "Rendimiento medio",
    "aistats.toReview": "A revisar",
    "aistats.bySurface": "Por superficie",
    "aistats.byTour": "Por tour",
    "aistats.byConfidence": "Por confianza modelo",
    "aistats.bySport": "Por deporte",
    "aistats.confidence": "Confianza",
    "aistats.recentHistory": "Historial reciente",
    "aistats.edge": "edge",
    "aistats.cta.label": "Varion Pro",
    "aistats.cta.title": "Acceso completo a las predicciones IA",
    "aistats.cta.descGood": "Nuestra IA muestra un track record solido. Suscribete para acceder a todos los value bets en tiempo real, historial completo y alertas moviles.",
    "aistats.cta.descNeutral": "Sigue el rendimiento de nuestra IA, recibe los value bets en tiempo real y el historial completo con Varion Pro.",
    "aistats.cta.winRate": "Tasa acierto IA",
    "aistats.cta.roi": "ROI medio",
    "aistats.cta.edge": "Edge medio",
    "aistats.cta.button": "Suscribirse a Varion Pro",
    "aistats.cta.disclaimer": "Apuesta de forma responsable. 18+. El rendimiento pasado no garantiza resultados futuros.",

    "aistats.import.title": "Importar archivo de seguimiento",
    "aistats.import.desc": "Suelta tu archivo suivi_varion.xlsx para actualizar las stats. Las apuestas existentes se actualizan, las nuevas se anaden.",
    "aistats.import.cta": "Suelta tu .xlsx aqui o haz clic para seleccionar",
    "aistats.import.drop": "Suelta el archivo aqui",
    "aistats.import.loading": "Leyendo archivo...",
    "aistats.import.success": "apuestas importadas con exito",
    "aistats.import.errFormat": "Formato invalido: solo .xlsx y .xls son aceptados",
    "aistats.import.errEmpty": "No se encontraron apuestas en el archivo",
    "aistats.import.errParse": "Error de lectura",
    "aistats.importedStats": "Stats desde archivo importado",
    "aistats.clearImport": "Borrar import",
    "aistats.importedPrincipales": "Predicciones principales",
    "aistats.importedRecommandees": "Apuestas recomendadas",
    "aistats.winRateWinner": "Tasa acierto ganador",
    "aistats.scoreExact": "% Marcador exacto",
    "aistats.gamesOver": "% Juegos Over",
  },
};


// État courant lang (lu depuis localStorage si dispo)
window.__VARION_LANG = (() => {
  try {
    const saved = localStorage.getItem("varion_lang");
    if (saved && window.I18N_DICTIONARIES[saved]) return saved;
  } catch (e) {}
  // Detecte langue navigateur
  const nav = (navigator.language || "fr").substring(0, 2).toLowerCase();
  if (window.I18N_DICTIONARIES[nav]) return nav;
  return "fr";
})();


// ========== TRADUCTIONS DONNEES API (surfaces, formats, etc.) ==========
window.API_TRANSLATIONS = {
  fr: {
    // Surfaces
    "hard": "Dur", "clay": "Terre battue", "grass": "Gazon", "indoor hard": "Dur indoor", "carpet": "Moquette",
    // Tournament tiers
    "Grand Slam": "Grand Chelem", "Masters 1000": "Masters 1000", "ATP 500": "ATP 500", "ATP 250": "ATP 250",
    "WTA 1000": "WTA 1000", "WTA 500": "WTA 500", "WTA 250": "WTA 250",
    "Other": "Autre", "Tour Finals": "Masters de fin d'annee",
    "Challenger": "Challenger", "Davis Cup": "Coupe Davis",
    // Rounds
    "Final": "Finale", "Semi-final": "Demi-finale", "Quarter-final": "Quart de finale",
    "Round of 16": "8e de finale", "Round of 32": "16e de finale",
    "Round of 64": "32e de finale", "Round of 128": "1er tour",
    "1st Round": "1er tour", "2nd Round": "2e tour", "3rd Round": "3e tour",
    // Plays / mains
    "Right-Handed": "Droitier", "Left-Handed": "Gaucher",
    "Two-Handed Backhand": "Revers a deux mains", "One-Handed Backhand": "Revers a une main",
    // Format
    "BO3": "BO3 (3 sets)", "BO5": "BO5 (5 sets)",
    // Pays courants (birthplace contient "Ville, Country")
    "Serbia": "Serbie", "France": "France", "Spain": "Espagne", "Italy": "Italie", "Germany": "Allemagne",
    "Switzerland": "Suisse", "Russia": "Russie", "United States": "Etats-Unis", "United Kingdom": "Royaume-Uni",
    "Argentina": "Argentine", "Australia": "Australie", "Croatia": "Croatie", "Greece": "Grece",
    "Hungary": "Hongrie", "Bulgaria": "Bulgarie", "Czech Republic": "Republique tcheque",
    "Belgium": "Belgique", "Netherlands": "Pays-Bas", "Poland": "Pologne", "Romania": "Roumanie",
    "Norway": "Norvege", "Denmark": "Danemark", "Sweden": "Suede", "Finland": "Finlande",
    "Canada": "Canada", "Brazil": "Bresil", "Chile": "Chili", "Mexico": "Mexique",
    "Japan": "Japon", "China": "Chine", "South Korea": "Coree du Sud", "India": "Inde",
    "Bosnia and Herzegovina": "Bosnie-Herzegovine", "Slovakia": "Slovaquie", "Slovenia": "Slovenie",
    "Austria": "Autriche", "Portugal": "Portugal", "Ireland": "Irlande", "Ukraine": "Ukraine",
    "Kazakhstan": "Kazakhstan", "Tunisia": "Tunisie", "South Africa": "Afrique du Sud",
    "Israel": "Israel", "Turkey": "Turquie", "Egypt": "Egypte",
    // Confidence levels
    "strong": "Forte", "high": "Elevee", "medium": "Moyenne", "model_only": "Modele",
  },

  en: {
    "hard": "Hard", "clay": "Clay", "grass": "Grass", "indoor hard": "Indoor hard", "carpet": "Carpet",
    "Grand Slam": "Grand Slam", "Masters 1000": "Masters 1000", "ATP 500": "ATP 500", "ATP 250": "ATP 250",
    "WTA 1000": "WTA 1000", "WTA 500": "WTA 500", "WTA 250": "WTA 250",
    "Other": "Other", "Tour Finals": "Tour Finals",
    "Challenger": "Challenger", "Davis Cup": "Davis Cup",
    "Final": "Final", "Semi-final": "Semi-final", "Quarter-final": "Quarter-final",
    "Round of 16": "Round of 16", "Round of 32": "Round of 32",
    "Round of 64": "Round of 64", "Round of 128": "Round of 128",
    "1st Round": "1st Round", "2nd Round": "2nd Round", "3rd Round": "3rd Round",
    "Right-Handed": "Right-Handed", "Left-Handed": "Left-Handed",
    "Two-Handed Backhand": "Two-Handed Backhand", "One-Handed Backhand": "One-Handed Backhand",
    "BO3": "BO3 (3 sets)", "BO5": "BO5 (5 sets)",
    "strong": "Strong", "high": "High", "medium": "Medium", "model_only": "Model",
  },

  es: {
    "hard": "Dura", "clay": "Tierra batida", "grass": "Hierba", "indoor hard": "Dura indoor", "carpet": "Moqueta",
    "Grand Slam": "Grand Slam", "Masters 1000": "Masters 1000", "ATP 500": "ATP 500", "ATP 250": "ATP 250",
    "WTA 1000": "WTA 1000", "WTA 500": "WTA 500", "WTA 250": "WTA 250",
    "Other": "Otro", "Tour Finals": "Final de la Gira",
    "Challenger": "Challenger", "Davis Cup": "Copa Davis",
    "Final": "Final", "Semi-final": "Semifinal", "Quarter-final": "Cuartos de final",
    "Round of 16": "Octavos de final", "Round of 32": "Dieciseisavos de final",
    "Round of 64": "Trigesimo segundos", "Round of 128": "Primera ronda",
    "1st Round": "Primera ronda", "2nd Round": "Segunda ronda", "3rd Round": "Tercera ronda",
    "Right-Handed": "Diestro", "Left-Handed": "Zurdo",
    "Two-Handed Backhand": "Reves a dos manos", "One-Handed Backhand": "Reves a una mano",
    "BO3": "BO3 (3 sets)", "BO5": "BO5 (5 sets)",
    "Serbia": "Serbia", "France": "Francia", "Spain": "Espana", "Italy": "Italia", "Germany": "Alemania",
    "Switzerland": "Suiza", "Russia": "Rusia", "United States": "Estados Unidos", "United Kingdom": "Reino Unido",
    "Argentina": "Argentina", "Australia": "Australia", "Croatia": "Croacia", "Greece": "Grecia",
    "Hungary": "Hungria", "Bulgaria": "Bulgaria", "Czech Republic": "Republica Checa",
    "Belgium": "Belgica", "Netherlands": "Paises Bajos", "Poland": "Polonia", "Romania": "Rumania",
    "Norway": "Noruega", "Denmark": "Dinamarca", "Sweden": "Suecia", "Finland": "Finlandia",
    "Canada": "Canada", "Brazil": "Brasil", "Chile": "Chile", "Mexico": "Mexico",
    "Japan": "Japon", "China": "China", "South Korea": "Corea del Sur", "India": "India",
    "strong": "Fuerte", "high": "Alta", "medium": "Media", "model_only": "Modelo",
  },
};


// Helper de traduction de donnees API
window.tApi = function (text) {
  if (!text) return "";
  const dict = window.API_TRANSLATIONS[window.__VARION_LANG] || window.API_TRANSLATIONS.fr;
  return dict[text] || dict[text.toLowerCase()] || text;
};


// Helper specifique : traduit une description "plays" type "Right-Handed, Two-Handed Backhand"
window.tPlays = function (plays) {
  if (!plays) return "";
  const parts = plays.split(",").map(p => p.trim()).map(window.tApi);
  return parts.join(", ");
};


// Helper specifique : traduit un birthplace "Belgrade, Serbia" -> traduit "Serbia" si possible
window.tBirthplace = function (birthplace) {
  if (!birthplace) return "";
  const parts = birthplace.split(",").map(p => p.trim());
  if (parts.length === 2) {
    return parts[0] + ", " + window.tApi(parts[1]);
  }
  return birthplace;
};


// Helper de traduction
window.t = function (key, fallback) {
  const dict = window.I18N_DICTIONARIES[window.__VARION_LANG] || window.I18N_DICTIONARIES.fr;
  return dict[key] || fallback || key;
};


// Setter de langue (appel depuis le selecteur)
window.setLang = function (lang) {
  if (!window.I18N_DICTIONARIES[lang]) return;
  window.__VARION_LANG = lang;
  try {
    localStorage.setItem("varion_lang", lang);
  } catch (e) {}
  // Force re-render via un event
  window.dispatchEvent(new Event("varion-lang-change"));
};


// État courant theme (lu depuis localStorage)
window.__VARION_THEME = (() => {
  try {
    const saved = localStorage.getItem("varion_theme");
    if (saved === "light" || saved === "dark") return saved;
  } catch (e) {}
  return "dark";
})();


// Setter de theme
window.setTheme = function (theme) {
  if (theme !== "light" && theme !== "dark") return;
  window.__VARION_THEME = theme;
  try {
    localStorage.setItem("varion_theme", theme);
  } catch (e) {}
  if (theme === "light") {
    document.documentElement.setAttribute("data-theme", "light");
  } else {
    document.documentElement.removeAttribute("data-theme");
  }
};

// Application immediate du theme stocke
if (typeof document !== "undefined" && window.__VARION_THEME === "light") {
  document.documentElement.setAttribute("data-theme", "light");
}
