#!/usr/bin/env bash
# cron_runner.sh - Lance un job de refresh + push sur GitHub
#
# Usage : bash cron_runner.sh foot|tennis
#
# Variables d'env attendues :
#   RAPIDAPI_KEY      : cle RapidAPI (Matchstat tennis + SportAPI7 foot)
#   GITHUB_TOKEN      : Personal Access Token GitHub avec scope 'repo'
#   GITHUB_REPO       : owner/nom (ex: DraZ89/varion)
#   GITHUB_BRANCH     : branche cible (ex: main)

set -e  # exit on first error

JOB_TYPE="${1:-foot}"

echo "=================================================="
echo "VARION CRON RUNNER - $JOB_TYPE"
echo "Date : $(date -u)"
echo "=================================================="

# Verifier les vars d'env
if [ -z "$RAPIDAPI_KEY" ]; then
  echo "ERREUR : RAPIDAPI_KEY non definie"
  exit 1
fi
if [ -z "$GITHUB_TOKEN" ]; then
  echo "ERREUR : GITHUB_TOKEN non definie"
  exit 1
fi
GITHUB_REPO="${GITHUB_REPO:-DraZ89/varion}"
GITHUB_BRANCH="${GITHUB_BRANCH:-main}"

# Aller dans le dossier backend
cd "$(dirname "$0")"
echo "Dossier courant : $(pwd)"

# Lancer le bon job
case "$JOB_TYPE" in
  foot)
    echo ">>> Lancement refresh_sportapi7 --prod"
    python -m jobs.refresh_sportapi7 --prod
    DATA_FILE="../frontend/data.json"
    COMMIT_MSG="chore: weekly foot data refresh [skip ci]"
    ;;
  tennis)
    echo ">>> Lancement refresh_tennis"
    python -m jobs.refresh_tennis
    DATA_FILE="../frontend/data_tennis.json"
    COMMIT_MSG="chore: daily tennis data refresh [skip ci]"
    ;;
  *)
    echo "ERREUR : type de job inconnu '$JOB_TYPE'. Use 'foot' or 'tennis'"
    exit 1
    ;;
esac

# Verifier que le fichier de data existe et n'est pas vide
if [ ! -s "$DATA_FILE" ]; then
  echo "ERREUR : $DATA_FILE est vide ou n'existe pas. Job echoue."
  exit 2
fi

DATA_SIZE=$(stat -c%s "$DATA_FILE" 2>/dev/null || stat -f%z "$DATA_FILE")
echo "OK $DATA_FILE genere ($DATA_SIZE octets)"

# Configuration git
echo ""
echo ">>> Configuration git"
git config user.email "bot@varion.app"
git config user.name "Varion Bot"

# Aller a la racine du repo (le job tourne dans backend/)
cd ..

# Cloner ou pull le repo le plus recent (eviter les conflits)
# Sur Render, le filesystem est ephemere donc on pourrait avoir besoin de re-cloner
# Mais en pratique, le cron run dans le repo deja clone par le build step.

git status

# Stager le fichier modifie
git add "${DATA_FILE#../}"  # enlever le ../ du chemin

# Verifier s'il y a vraiment qqch a commit
if git diff --staged --quiet; then
  echo "Pas de changement dans $DATA_FILE, on skip le commit."
  exit 0
fi

# Commit + push
git commit -m "$COMMIT_MSG"
git push "https://${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git" "HEAD:${GITHUB_BRANCH}"

echo ""
echo "=================================================="
echo "OK Cron $JOB_TYPE termine avec succes"
echo "=================================================="
