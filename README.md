# VARION — Sports Betting Analytics

Application complète d'analyse de paris sportifs combinant analyse statistique d'équipe, analyse individuelle des joueurs, et détection automatique de **value bets** sur 12+ marchés.

---

## ⚡ Démarrage rapide (3 étapes)

### 1) Télécharger les logos officiels des clubs

```bash
python download_logos.py
```

Récupère les SVG officiels depuis Wikipedia (Manchester City, Arsenal, Liverpool, Chelsea, Tottenham, Manchester United, Newcastle, Aston Villa, Brighton, West Ham) dans `frontend/logos/`.

### 2) Construire le standalone HTML

```bash
python build_standalone.py
```

Génère `varion_standalone.html` avec **tout inline** : code, styles, données pré-calculées, **et les 10 logos SVG officiels embarqués**. Aucun serveur, aucune dépendance réseau.

### 3) Ouvrir le fichier

Double-clic sur `varion_standalone.html`. C'est tout.

---

## 🚀 Déploiement Netlify

### Méthode drag & drop

```bash
python download_logos.py
```

Puis sur [app.netlify.com/drop](https://app.netlify.com/drop), glisse-dépose le dossier `frontend/` complet.

### Méthode Git

Push le repo sur GitHub, connecte-le à Netlify. Pense à exécuter `download_logos.py` une fois et à committer le dossier `frontend/logos/` (les SVG ne pèsent que ~5-30 KB chacun).

---

## 📂 Architecture

```
betting-app/
├── download_logos.py         # ⬇️  Télécharge les logos officiels
├── build_standalone.py       # 🔧 Construit le HTML inline
├── varion_standalone.html    # 📦 Build standalone (généré)
│
├── backend/
│   ├── main.py               # API FastAPI (6 endpoints)
│   ├── data/                 # teams.py, players.py, matches.py
│   └── engine/               # team_analysis, player_analysis, predictions, value_bets, summary
│
└── frontend/
    ├── index.html
    ├── styles.css
    ├── data.json             # Données pré-calculées
    ├── logos/                # ⚽ SVG officiels (généré)
    └── src/components/       # Common.js, MatchCard, MatchDetail, ValueBets, App
```

---

## 🎯 Mode complet (backend + frontend)

```bash
# Terminal 1 : backend
cd backend
pip install -r requirements.txt
python main.py        # http://localhost:8000

# Terminal 2 : frontend
cd frontend
python -m http.server 8080    # http://localhost:8080
```

Le frontend détecte automatiquement le backend ; sinon il bascule sur `data.json`.

---

## 🧠 Le moteur d'analyse

### Scores équipes (0–100)

| Score | Calcul |
|---|---|
| **Forme** | Pondération exponentielle des 10 derniers résultats |
| **Attaque** | 30% buts/match + 30% xG + 20% tirs cadrés + 20% Over 2.5% |
| **Défense** | 35% buts encaissés (inverse) + 35% xGA (inverse) + 30% clean sheets |
| **Qualité effectif** | Forme moyenne du XI type sur 5 matchs |
| **Stabilité XI** | Ratio moyen titularisations/matchs joués des 11 titulaires |
| **Score global** | Pondération 25/25/25/15/10 |

### Modèle prédictif (Poisson bivarié type Dixon-Coles)

```
λ_home = league_avg_home × (xg_home / league_avg) × (xga_away / league_avg)
       × home_factor × form_factor × h2h_factor
```

Marchés dérivés : 1X2, BTTS, Over/Under 2.5/3.5, clean sheets, corners, cartons, buteurs.

### Value Bet Engine

```python
edge = (probabilité_modèle × cote) - 1
```

Niveaux : 🔥 strong (>15%), ✅ high (8-15%), 💡 moderate (3-8%).

---

## 🎨 Interface Varion

Esthétique **"data terminal / trading desk"** :
- Typo Bebas Neue + JetBrains Mono + Manrope
- Palette sombre + accent lime électrique (`#d4ff3f`)
- Logos officiels SVG haute résolution

**Pages** :
1. **Dashboard** — matchs avec preview prédictions + top value bet
2. **Page Match (8 sections)** — synthèse, équipes, compositions, joueurs clés, gardiens, marchés, value bets, H2H
3. **Value Bets agrégés** — toutes opportunités triées par edge
4. **Classement** Premier League

---

## ⚖️ À propos des logos

Les logos officiels sont téléchargés depuis Wikipedia/Wikimedia Commons. Ils sont protégés par le copyright des clubs respectifs et utilisés ici dans un cadre éducatif/personnel. Pour un usage commercial, vérifie les conditions de chaque club.

---

## 🔌 Brancher des données réelles

Le moteur est agnostique de la source. Remplace `backend/data/teams.py`, `players.py`, `matches.py` par des fetchers d'API :
- **API-Football** → données live
- **FBRef / Understat** → xG, xGA détaillés
- **The Odds API** → cotes bookmakers temps réel

---

## 📝 Licence

MIT — Code uniquement. Les logos appartiennent à leurs propriétaires respectifs.
