# Setup Google Sheets ↔ Varion (sync bidirectionnelle)

## 🎯 Ce que tu vas avoir à la fin

- **Auto-sync matinal** : tous les jours à 8h, ton Sheet récupère les paris IA du jour
- **Bouton "Envoyer les résultats"** : tu rentres les résultats dans ton Sheet, tu cliques, ils arrivent dans la DB du site
- **Aucun risque pour le data existant** : juste une nouvelle colonne `match_id` cachée pour la sync

---

## 📋 Prérequis

- Ton site Varion est en ligne (Render + GH Pages) ✅
- Ton Google Sheet `suivi_varion_corrige.xlsx` est ouvert dans Google Sheets

---

## Étape 1 — Générer un SHEETS_TOKEN (1 min)

Ouvre PowerShell et tape :
```powershell
[guid]::NewGuid().ToString() + [guid]::NewGuid().ToString()
```

Tu obtiens un truc du genre `a1b2c3d4-...-9876`. **Copie-le**, garde-le.

---

## Étape 2 — Ajouter SHEETS_TOKEN dans Render (2 min)

1. https://dashboard.render.com → `varion-backend` → menu **Environment**
2. **Add Environment Variable** :
   - Key : `SHEETS_TOKEN`
   - Value : (ton token de l'étape 1)
3. **Save Changes** → Render redéploie automatiquement (~1 min)

---

## Étape 3 — Préparer le Google Sheet (1 min)

1. Ouvre ton Google Sheet (`suivi_varion_corrige`)
2. Va sur l'onglet **Raw Data**
3. **Cellule U1** : tape `match_id`
4. **Sélectionne la colonne U** (clic sur l'en-tête "U") → clic droit → **Masquer la colonne**

Cette colonne sera utilisée par l'Apps Script pour suivre quels paris sont déjà importés. Tu la caches pour ne pas la voir.

---

## Étape 4 — Coller l'Apps Script (3 min)

1. Dans ton Google Sheet : **Extensions** → **Apps Script**
2. Tu arrives sur un éditeur de code avec un fichier `Code.gs` vide ou avec `function myFunction() {}`
3. **Sélectionne TOUT le code existant** (Ctrl+A) → **Supprime** (Suppr)
4. **Ouvre le fichier `varion-sheets-sync.gs`** (celui livré dans le zip)
5. **Copie tout son contenu** et **colle** dans l'éditeur Apps Script
6. **Sauvegarde** : icône 💾 ou Ctrl+S
   - Si demandé : nomme le projet `Varion Sync`

---

## Étape 5 — Configurer le SHEETS_TOKEN dans Apps Script (1 min)

1. Toujours dans Apps Script : menu gauche → **Paramètres du projet** (icône ⚙️)
2. Scroll en bas → **Propriétés du script** → **Ajouter une propriété**
3. Renseigne :
   - **Property** : `SHEETS_TOKEN`
   - **Value** : (le même token que tu as mis dans Render à l'étape 2)
4. **Save script properties**

---

## Étape 6 — Autoriser l'Apps Script (1 min)

1. Retourne sur l'éditeur Apps Script
2. En haut, dropdown des fonctions → sélectionne **`syncFromVarion`**
3. Clique **▶️ Exécuter**
4. Google demande des autorisations :
   - Compte → choisis le tien
   - "Cette application n'a pas été vérifiée par Google" → clique **Paramètres avancés** → **Accéder à Varion Sync**
   - **Autoriser** : Edit Sheets + Faire des requêtes externes

L'autorisation se fait une fois pour toutes.

---

## Étape 7 — Premier import + activer auto-sync (1 min)

1. Retourne sur le Google Sheet
2. Tu vois maintenant un nouveau menu **🎾 Varion** dans la barre supérieure
   - Si non visible : **recharge la page** du Sheet (F5)
3. Clique **🎾 Varion → Importer les paris IA**
   - Si tout marche : message vert avec le nombre de paris importés ✅
   - Les nouvelles lignes apparaissent dans Raw Data
4. Clique **🎾 Varion → Activer l'auto-sync matinal**
   - Maintenant le Sheet récupère les paris IA tous les jours à 8h automatiquement

---

## 🎉 Utilisation quotidienne

### Matin (8h auto)
Les paris IA du jour arrivent dans Raw Data.

### Soir / Après les matchs
Pour chaque match joué, tu remplis dans Raw Data :
- **Colonne G** : Vainqueur réel
- **Colonne I** : Score réel (ex `2-0`)
- **Colonne K** : Jeux réels (ex `19`)
- Pour les Recommandées : **Colonne O** : `Gagné` ou `Perdu`

### Envoyer les résultats au site
Quand tu as fini de remplir : **🎾 Varion → Envoyer les résultats**
→ Les paris sont marqués Gagné/Perdu dans la DB du site
→ La page Performance IA se met à jour

---

## 🆘 Troubleshooting

### "❌ SHEETS_TOKEN non configuré"
Étape 5 pas faite. Va dans Script Properties d'Apps Script et ajoute `SHEETS_TOKEN`.

### "❌ Backend erreur 403"
Le token du Sheet ≠ celui de Render. Vérifie qu'ils sont identiques.

### "❌ Backend erreur 401"
Le header Authorization n'est pas envoyé. Re-essaie, ou vérifie que l'Apps Script est bien le bon (re-coller).

### Menu "🎾 Varion" invisible
Recharge le Sheet (F5). Si toujours invisible, l'`onOpen()` n'a pas fonctionné. Va dans Apps Script et exécute manuellement `onOpen()`.

### "Erreur Cell U vide" ou paris dupliqués
Tu as supprimé une ligne avec son match_id. Pas grave, la prochaine sync les ajoutera à nouveau.

### Auto-sync n'a pas tourné à 8h
- Apps Script → Triggers (icône ⏰ gauche) → vérifie qu'il y a bien un trigger sur `syncFromVarion` toutes les 24h
- Si pas là : relance **🎾 Varion → Activer l'auto-sync matinal**

---

## 🔐 Sécurité

- Le `SHEETS_TOKEN` te protège : seul ton Apps Script peut accéder aux endpoints `/api/sheets/...`
- Le token n'est jamais affiché dans Google Sheets (stocké dans Script Properties)
- Si quelqu'un récupère ton Sheet, il a ton tracking mais pas ton token
- Tu peux **régénérer le token** à tout moment :
  1. Génère un nouveau token (Étape 1)
  2. Mets-le à jour dans Render env vars ET Script Properties
