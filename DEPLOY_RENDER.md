# Déploiement Varion : Frontend GitHub Pages + Backend Render

Architecture :
- **Frontend statique** sur GitHub Pages (URL : `https://draz89.github.io/varion/`)
- **Backend FastAPI** sur Render Free (URL : `https://varion-backend.onrender.com`)
- **Cron jobs** via cron-job.org (gratuit, ping les endpoints admin du backend)

---

## ⚠️ AVANT TOUT : Régénère tes credentials

Tu as déjà collé tes credentials dans des conversations précédentes :
- Webhook Discord
- Clé RapidAPI

**Régénère-les maintenant** avant de déployer :
- Discord : Salon → Intégrations → Webhooks → supprimer + créer
- RapidAPI : Dashboard → ton compte → API Keys → Regenerate

---

## Étape 1 — Push à jour sur GitHub

```powershell
cd C:\Users\cory8\OneDrive\Desktop\Varion\betting-app
git add .
git commit -m "Deploy: Render backend + GitHub Pages frontend"
git push
```

---

## Étape 2 — Déployer le backend sur Render

1. Va sur https://dashboard.render.com
2. **"New +" → "Web Service"**
3. Connecte ton repo GitHub `DraZ89/varion`
4. Configuration :
   - **Name** : `varion-backend`
   - **Region** : `Frankfurt (EU Central)`
   - **Branch** : `main`
   - **Root Directory** : `backend`
   - **Runtime** : `Python 3`
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan** : `Free`
5. **Environment Variables** :
   - `RAPIDAPI_KEY` = ta clé RapidAPI (régénérée !)
   - `DISCORD_WEBHOOK_URL` = ton URL webhook (régénéré !)
   - `ADMIN_TOKEN` = un token aléatoire à générer toi-même

   **Générer un token avec PowerShell** :
   ```powershell
   [guid]::NewGuid().ToString() + [guid]::NewGuid().ToString()
   ```
   Copie le résultat (genre `a1b2c3d4-e5f6-...-9876`) pour `ADMIN_TOKEN`. **Garde-le précieusement**, tu en auras besoin pour cron-job.org.

6. Clique **"Create Web Service"** → Render build (~3-5 min)

7. Une fois terminé : note l'URL exacte que Render te donne (genre `https://varion-backend.onrender.com`)

---

## Étape 3 — Configurer le frontend pour pointer vers ton backend Render

Si l'URL Render n'est pas `https://varion-backend.onrender.com`, il faut éditer **frontend/index.html** :

```html
} else if (host.endsWith("github.io")) {
  window.API_BASE = "https://TON-URL-RENDER.onrender.com";  // <-- modifier ici
}
```

Push après modification :

```powershell
git add frontend/index.html
git commit -m "Set backend URL"
git push
```

---

## Étape 4 — Activer GitHub Pages

1. Va sur https://github.com/DraZ89/varion/settings/pages
2. **Source** : choisir **"GitHub Actions"** (pas "Deploy from branch")
3. Le workflow `.github/workflows/deploy-pages.yml` est déjà inclus dans ton repo
4. Va sur l'onglet **"Actions"** de ton repo : tu vois le workflow tourner
5. Une fois terminé (~1 min) : ton site est sur `https://draz89.github.io/varion/`

---

## Étape 5 — Premier refresh manuel

Pour générer les données tennis sur le backend :

```powershell
$token = "TON_ADMIN_TOKEN"
Invoke-RestMethod -Uri "https://varion-backend.onrender.com/api/admin/refresh-tennis" -Method Post -Headers @{Authorization = "Bearer $token"}
```

Attendre ~30s, puis recharger `https://draz89.github.io/varion/` → tu devrais voir les matchs.

---

## Étape 6 — Configurer cron-job.org

1. Va sur https://cron-job.org → crée un compte gratuit
2. **Create cronjob** x3 :

### Job 1 : Refresh tennis (2× par jour)
- **Title** : `Varion Refresh Tennis`
- **URL** : `https://varion-backend.onrender.com/api/admin/refresh-tennis`
- **Method** : `POST`
- **Schedule** : `Custom` → `0 7,19 * * *` (7h et 19h UTC, donc 8h et 20h en France hiver)
- **Headers** :
  - Name : `Authorization`
  - Value : `Bearer TON_ADMIN_TOKEN`

### Job 2 : Resolve bets (1× par jour)
- **Title** : `Varion Resolve Bets`
- **URL** : `https://varion-backend.onrender.com/api/admin/resolve-bets`
- **Method** : `POST`
- **Schedule** : `Custom` → `0 23 * * *` (23h UTC)
- **Headers** : `Authorization: Bearer TON_ADMIN_TOKEN`

### Job 3 : Keep-alive (toutes les 10min)
**Empêche le sleep du backend Render Free**.
- **Title** : `Varion Keep Alive`
- **URL** : `https://varion-backend.onrender.com/`
- **Method** : `GET`
- **Schedule** : Every 10 minutes
- Pas de headers

---

## Étape 7 — Tests fonctionnels

- [ ] `https://draz89.github.io/varion/` charge
- [ ] Onglet Tennis affiche les matchs
- [ ] Page détail d'un match marche
- [ ] Page Performance IA affiche les stats
- [ ] Toggle dark/light marche
- [ ] Sélecteur langue marche
- [ ] Drag & drop xlsx sur Performance IA marche

---

## Troubleshooting

**"Failed to fetch" partout dans la console** : le frontend ne trouve pas le backend.
→ Vérifie l'URL Render dans `frontend/index.html` ligne `window.API_BASE`.

**Page Tennis vide** : pas encore de données.
→ Lance le refresh manuel de l'étape 5.

**"Invalid admin token"** : le token dans cron-job.org ne matche pas celui de Render.
→ Vérifie dans Render Dashboard → ton service → "Environment" → valeur de `ADMIN_TOKEN`.

**1ère requête API très lente (>30s)** : c'est le cold start du Free tier.
→ Le cron Keep-alive (job 3) règle ça après 10-15 min.

**Discord ne reçoit pas les picks** : check le webhook dans env Render.
→ Test : appelle `/api/admin/refresh-tennis` et regarde les logs Render.

**Quota RapidAPI** : check ton dashboard, plan Pro = 10k/mois.
→ 2 refresh/jour × ~50 req = 3000/mois (largement sous le plafond).

---

## URLs utiles

- Site (utilisateurs) : `https://draz89.github.io/varion/`
- API backend : `https://varion-backend.onrender.com`
- Dashboard Render : `https://dashboard.render.com`
- cron-job.org : `https://console.cron-job.org/jobs`
- GitHub Actions : `https://github.com/DraZ89/varion/actions`
