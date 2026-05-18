/**
 * VARION SYNC — Apps Script pour Google Sheets
 *
 * À coller dans : Extensions → Apps Script → remplacer tout le code
 *
 * Setup nécessaire :
 *   1. Dans Google Sheets : Extensions → Apps Script
 *   2. Coller ce code → Sauvegarder (icône disquette)
 *   3. Configurer Script Properties (clé en bas du code)
 *   4. Lancer setupTrigger() une fois pour activer l'auto-sync matinal
 *   5. Recharger le Sheet → menu "🎾 Varion" doit apparaître
 */

// ============== CONFIG ==============

const BACKEND_URL = "https://varion-backend.onrender.com";
// SHEETS_TOKEN à configurer dans Script Properties (voir setupInstructions())
const RAW_DATA_SHEET = "Raw Data";

// Colonnes Raw Data (1-indexées : A=1, B=2, ...)
const COL = {
  DATE: 1,             // A
  MATCH: 2,            // B
  TOURNAMENT: 3,       // C
  PLAYER_A: 4,         // D
  PLAYER_B: 5,         // E
  PREDICTED_WINNER: 6, // F
  REAL_WINNER: 7,      // G
  PREDICTED_SCORE: 8,  // H
  REAL_SCORE: 9,       // I
  PREDICTED_GAMES: 10, // J
  REAL_GAMES: 11,      // K
  TYPE: 12,            // L
  BET_LABEL: 13,       // M
  ODDS: 14,            // N
  BET_RESULT: 15,      // O
  SURFACE: 16,         // P
  TIER: 17,            // Q
  WINNER_OK: 18,       // R
  SCORE_OK: 19,        // S
  GAMES_OK: 20,        // T
  MATCH_ID: 21,        // U (caché, pour sync)
};


// ============== MENU CUSTOM ==============

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("🎾 Varion")
    .addItem("⬇️ Importer les paris IA", "syncFromVarion")
    .addItem("⬆️ Envoyer les résultats", "sendResultsToVarion")
    .addSeparator()
    .addItem("⚙️ Activer l'auto-sync matinal", "setupTrigger")
    .addItem("📖 Instructions de setup", "showSetupInstructions")
    .addToUi();
}


// ============== SITE → SHEET (import paris IA) ==============

/**
 * Va chercher les paris IA depuis le backend et les ajoute à Raw Data.
 * Skip les paris déjà présents (match_id dans col U).
 */
function syncFromVarion() {
  const token = PropertiesService.getScriptProperties().getProperty("SHEETS_TOKEN");
  if (!token) {
    SpreadsheetApp.getUi().alert("❌ SHEETS_TOKEN non configuré dans Script Properties.");
    return;
  }

  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(RAW_DATA_SHEET);
  if (!sheet) {
    SpreadsheetApp.getUi().alert(`❌ Onglet "${RAW_DATA_SHEET}" introuvable.`);
    return;
  }

  // 1. Récupérer les match_id déjà présents (col U)
  const lastRow = sheet.getLastRow();
  const existingIds = new Set();
  if (lastRow >= 2) {
    const ids = sheet.getRange(2, COL.MATCH_ID, lastRow - 1, 1).getValues();
    ids.forEach(row => {
      if (row[0]) existingIds.add(String(row[0]).trim());
    });
  }

  // 2. Fetch backend
  let bets;
  try {
    const response = UrlFetchApp.fetch(BACKEND_URL + "/api/sheets/pending-bets", {
      method: "get",
      headers: { "Authorization": "Bearer " + token },
      muteHttpExceptions: true,
    });
    const code = response.getResponseCode();
    if (code !== 200) {
      SpreadsheetApp.getUi().alert(`❌ Backend erreur ${code} : ${response.getContentText().substring(0, 200)}`);
      return;
    }
    bets = JSON.parse(response.getContentText());
  } catch (e) {
    SpreadsheetApp.getUi().alert("❌ Erreur réseau : " + e);
    return;
  }

  if (!Array.isArray(bets) || bets.length === 0) {
    SpreadsheetApp.getUi().alert("ℹ️ Aucun pari à importer (backend renvoie vide).");
    return;
  }

  // 3. Ajouter les nouveaux uniquement
  const newRows = [];
  bets.forEach(bet => {
    // Identifiant unique = match_id + type (un match peut avoir Principale + Recommandées)
    const uniqueId = (bet.match_id || "") + "_" + (bet.type || "");
    if (existingIds.has(uniqueId)) return;  // déjà présent

    const row = new Array(COL.MATCH_ID);  // tableau de la bonne taille
    row[COL.DATE - 1] = bet.date || "";
    row[COL.MATCH - 1] = `${bet.player_a} vs ${bet.player_b}`;
    row[COL.TOURNAMENT - 1] = bet.tournament || "";
    row[COL.PLAYER_A - 1] = bet.player_a || "";
    row[COL.PLAYER_B - 1] = bet.player_b || "";
    row[COL.PREDICTED_WINNER - 1] = bet.predicted_winner || "";
    row[COL.REAL_WINNER - 1] = "";  // à remplir manuellement
    row[COL.PREDICTED_SCORE - 1] = bet.predicted_score || "";
    row[COL.REAL_SCORE - 1] = "";
    row[COL.PREDICTED_GAMES - 1] = bet.predicted_games || "";
    row[COL.REAL_GAMES - 1] = "";
    row[COL.TYPE - 1] = bet.type || "Principale";
    row[COL.BET_LABEL - 1] = bet.bet_label || "";
    row[COL.ODDS - 1] = bet.odds || "";
    row[COL.BET_RESULT - 1] = "";
    row[COL.SURFACE - 1] = bet.surface || "";
    row[COL.TIER - 1] = bet.tier || bet.tour || "";
    row[COL.WINNER_OK - 1] = "";  // formules R/S/T se recopient
    row[COL.SCORE_OK - 1] = "";
    row[COL.GAMES_OK - 1] = "";
    row[COL.MATCH_ID - 1] = uniqueId;
    newRows.push(row);
  });

  if (newRows.length === 0) {
    SpreadsheetApp.getUi().alert(`ℹ️ Aucun nouveau pari (${bets.length} reçus, tous déjà présents).`);
    return;
  }

  // 4. Insérer en bas
  const startRow = lastRow + 1;
  sheet.getRange(startRow, 1, newRows.length, COL.MATCH_ID).setValues(newRows);

  // 5. Recopier les formules R, S, T depuis la ligne précédente s'il y en a une
  if (lastRow >= 2) {
    const formulaRow = sheet.getRange(lastRow, COL.WINNER_OK, 1, 3);
    const formulas = formulaRow.getFormulas()[0];
    if (formulas[0] || formulas[1] || formulas[2]) {
      for (let i = 0; i < newRows.length; i++) {
        const targetRow = startRow + i;
        ["WINNER_OK", "SCORE_OK", "GAMES_OK"].forEach((key, idx) => {
          if (formulas[idx]) {
            const newFormula = formulas[idx].replace(new RegExp(lastRow, "g"), targetRow);
            sheet.getRange(targetRow, COL[key]).setFormula(newFormula);
          }
        });
      }
    }
  }

  // 6. Coloriage : alternance verte/orange par jour + jaune pour Recommandées
  // On determine le pattern en regardant les jours dans toute la feuille
  applyAlternatingColors(sheet);

  SpreadsheetApp.getUi().alert(`✅ ${newRows.length} nouveau(x) pari(s) importé(s) depuis Varion.`);
}


/**
 * Applique l'alternance de couleurs sur toutes les lignes de Raw Data.
 * - Jour 1 = vert clair 3 (#d9ead3)
 * - Jour 2 = orange clair 3 (#fce5cd)
 * - Pari Recommandée = jaune clair 1 (#fff2cc) (override la couleur du jour)
 */
function applyAlternatingColors(sheet) {
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return;

  // Lire dates et types
  const data = sheet.getRange(2, 1, lastRow - 1, COL.TYPE).getValues();

  // Identifier les jours uniques dans l'ordre d'apparition
  const dayMap = new Map();
  let dayIndex = 0;
  data.forEach(row => {
    const dateVal = row[COL.DATE - 1];
    const dateKey = dateVal instanceof Date
      ? dateVal.toISOString().slice(0, 10)
      : String(dateVal).trim();
    if (dateKey && !dayMap.has(dateKey)) {
      dayMap.set(dateKey, dayIndex);
      dayIndex++;
    }
  });

  const COLOR_DAY_A = "#d9ead3";    // vert clair 3
  const COLOR_DAY_B = "#fce5cd";    // orange clair 3
  const COLOR_RECO = "#fff2cc";     // jaune clair 1

  // Construire le tableau de couleurs ligne par ligne
  const colors = data.map(row => {
    const type = String(row[COL.TYPE - 1] || "").trim();
    if (type === "Recommandée") {
      // Toute la ligne en jaune clair
      return new Array(COL.MATCH_ID).fill(COLOR_RECO);
    }
    const dateVal = row[COL.DATE - 1];
    const dateKey = dateVal instanceof Date
      ? dateVal.toISOString().slice(0, 10)
      : String(dateVal).trim();
    const idx = dayMap.get(dateKey);
    const color = (idx % 2 === 0) ? COLOR_DAY_A : COLOR_DAY_B;
    return new Array(COL.MATCH_ID).fill(color);
  });

  // Appliquer
  sheet.getRange(2, 1, colors.length, COL.MATCH_ID).setBackgrounds(colors);
}


// ============== SHEET → SITE (envoi résultats) ==============

/**
 * Parcourt les lignes avec un Real Winner ou Bet Result rempli mais pas encore envoyé,
 * et les envoie au backend pour mise à jour DB.
 */
function sendResultsToVarion() {
  const token = PropertiesService.getScriptProperties().getProperty("SHEETS_TOKEN");
  if (!token) {
    SpreadsheetApp.getUi().alert("❌ SHEETS_TOKEN non configuré dans Script Properties.");
    return;
  }

  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(RAW_DATA_SHEET);
  if (!sheet) {
    SpreadsheetApp.getUi().alert(`❌ Onglet "${RAW_DATA_SHEET}" introuvable.`);
    return;
  }

  const lastRow = sheet.getLastRow();
  if (lastRow < 2) {
    SpreadsheetApp.getUi().alert("ℹ️ Pas de données à envoyer.");
    return;
  }

  // Lire toutes les lignes
  const data = sheet.getRange(2, 1, lastRow - 1, COL.MATCH_ID).getValues();

  const results = [];
  data.forEach((row, idx) => {
    const matchId = String(row[COL.MATCH_ID - 1] || "").trim();
    if (!matchId) return;  // pas de match_id, skip

    const type = String(row[COL.TYPE - 1] || "Principale").trim();

    if (type === "Recommandée") {
      const betResult = String(row[COL.BET_RESULT - 1] || "").trim();
      if (!betResult) return;
      results.push({
        match_id: matchId.split("_")[0] + "_" + (matchId.includes("Recommandée") ? "" : ""),  // extraire vrai match_id
        type: "Recommandée",
        bet_result: betResult,
      });
    } else {
      const realWinner = String(row[COL.REAL_WINNER - 1] || "").trim();
      if (!realWinner) return;
      results.push({
        match_id: matchId.split("_")[0],  // extraire le vrai match_id (avant _Principale)
        type: "Principale",
        real_winner: realWinner,
        real_score: String(row[COL.REAL_SCORE - 1] || "").trim(),
        real_games: row[COL.REAL_GAMES - 1] || "",
      });
    }
  });

  if (results.length === 0) {
    SpreadsheetApp.getUi().alert("ℹ️ Aucun résultat à envoyer (colonnes G ou O vides).");
    return;
  }

  // POST au backend
  try {
    const response = UrlFetchApp.fetch(BACKEND_URL + "/api/sheets/submit-results", {
      method: "post",
      contentType: "application/json",
      headers: { "Authorization": "Bearer " + token },
      payload: JSON.stringify({ results: results }),
      muteHttpExceptions: true,
    });

    const code = response.getResponseCode();
    if (code !== 200) {
      SpreadsheetApp.getUi().alert(`❌ Backend erreur ${code} : ${response.getContentText().substring(0, 300)}`);
      return;
    }

    const result = JSON.parse(response.getContentText());
    const errMsg = (result.errors && result.errors.length > 0)
      ? `\n\n⚠️ Erreurs : ${result.errors.slice(0, 3).join(", ")}`
      : "";
    SpreadsheetApp.getUi().alert(`✅ ${result.updated} pari(s) mis à jour sur Varion (${result.total_received} envoyés).${errMsg}`);
  } catch (e) {
    SpreadsheetApp.getUi().alert("❌ Erreur réseau : " + e);
  }
}


// ============== AUTO-TRIGGER MATINAL ==============

/**
 * Active un trigger qui lance syncFromVarion() tous les jours à 8h du matin (heure du Sheet).
 */
function setupTrigger() {
  // Supprimer les triggers existants
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(t => {
    if (t.getHandlerFunction() === "syncFromVarion") {
      ScriptApp.deleteTrigger(t);
    }
  });

  // Créer un nouveau trigger : tous les jours à 8h
  ScriptApp.newTrigger("syncFromVarion")
    .timeBased()
    .everyDays(1)
    .atHour(8)
    .create();

  SpreadsheetApp.getUi().alert("✅ Auto-sync matinal activé. Le Sheet récupérera les paris IA tous les jours à 8h.");
}


// ============== INSTRUCTIONS SETUP ==============

function showSetupInstructions() {
  const html = HtmlService.createHtmlOutput(`
    <h2>🎾 Setup Varion Sync</h2>
    <ol>
      <li><b>Configurer SHEETS_TOKEN</b> :
        <ol type="a">
          <li>Apps Script → Project Settings (⚙️ gauche) → Script Properties → Add Script Property</li>
          <li>Property : <code>SHEETS_TOKEN</code></li>
          <li>Value : ton token (à demander à l'admin Varion)</li>
          <li>Save</li>
        </ol>
      </li>
      <li><b>Activer auto-sync matinal</b> : menu 🎾 Varion → Activer l'auto-sync matinal</li>
      <li><b>Premier import manuel</b> : menu 🎾 Varion → Importer les paris IA</li>
    </ol>
    <p><b>Utilisation quotidienne</b> :</p>
    <ul>
      <li>Les paris IA arrivent auto à 8h dans l'onglet Raw Data</li>
      <li>Tu remplis les colonnes G (vainqueur réel), I (score réel), K (jeux réels), O (résultat pari reco)</li>
      <li>Tu cliques sur 🎾 Varion → Envoyer les résultats → la DB du site se met à jour</li>
    </ul>
  `).setWidth(600).setHeight(450);
  SpreadsheetApp.getUi().showModalDialog(html, "Setup Varion");
}
