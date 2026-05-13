"""
Module d'envoi des picks tennis du jour vers un salon Discord via webhook.

Setup :
  1. Sur Discord : Salon -> "Modifier le salon" -> "Integrations" -> "Webhooks"
  2. "Nouveau webhook" -> "Copier l'URL"
  3. Mettre l'URL dans la variable d'env : DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

Usage :
  from integrations import discord_notifier
  discord_notifier.send_daily_picks(matches)
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

# Couleurs hexa par surface (decimal pour Discord)
SURFACE_COLORS = {
    "hard": 0x5B9DFF,         # bleu electric
    "clay": 0xE8743F,         # orange terre
    "grass": 0x73F5A1,        # vert
    "indoor hard": 0xA78BFA,  # violet IA
    "carpet": 0xC4B5FD,       # violet clair
}
DEFAULT_COLOR = 0xA78BFA  # violet IA par defaut

# Mapping surface label
SURFACE_LABELS = {
    "hard": "Hard",
    "clay": "Clay",
    "grass": "Grass",
    "indoor hard": "Indoor Hard",
    "carpet": "Carpet",
}


def _format_match_time(start_timestamp_ms):
    """Format epoch ms vers une chaine lisible (UTC)."""
    if not start_timestamp_ms:
        return "Heure non confirmee"
    try:
        dt = datetime.fromtimestamp(int(start_timestamp_ms) / 1000, tz=timezone.utc)
        # Discord affiche l'heure en local user via timestamps Discord
        unix_sec = int(int(start_timestamp_ms) / 1000)
        return f"<t:{unix_sec}:t> · <t:{unix_sec}:R>"  # 09:10 · dans 4h
    except Exception:
        return "Heure non confirmee"


def _build_match_embed(match: dict) -> dict:
    """Construit un embed Discord pour 1 match."""
    pa = match.get("player_a") or {}
    pb = match.get("player_b") or {}
    bets = match.get("value_bets") or []

    surface = (match.get("surface") or "hard").lower()
    color = SURFACE_COLORS.get(surface, DEFAULT_COLOR)
    surface_label = SURFACE_LABELS.get(surface, surface.title())

    # Titre : Joueur A vs Joueur B
    title = f"{pa.get('name', '?')}  vs  {pb.get('name', '?')}"

    # Description : tournoi + tier + format
    desc_parts = []
    if match.get("tournament"):
        desc_parts.append(f"**{match['tournament']}**")
    tier = match.get("tournament_type")
    if tier and tier != "Other":
        desc_parts.append(tier)
    fmt = match.get("format", "BO3")
    desc_parts.append(f"`{surface_label}` · `{fmt}`")
    description = " · ".join(desc_parts)

    # Predictions
    preds = match.get("predictions") or {}
    winner = preds.get("winner") or {}
    prob_a = winner.get("prob_a", 50)
    prob_b = winner.get("prob_b", 50)

    fields = []

    # Field 1 : probabilites du modele
    fav_name = pa.get("name") if prob_a >= prob_b else pb.get("name")
    fav_prob = max(prob_a, prob_b)
    fields.append({
        "name": "Modele IA",
        "value": (
            f"**{fav_name}** favori\n"
            f"`{prob_a:.0f}%` vs `{prob_b:.0f}%`"
        ),
        "inline": True,
    })

    # Field 2 : cotes (estimees ou reelles)
    odds = match.get("odds") or {}
    odd1 = odds.get("1")
    odd2 = odds.get("2")
    odds_source = odds.get("_source", "none")
    odds_label = "Cotes" if odds_source == "api" else "Cotes (est.)"
    if odd1 and odd2:
        fields.append({
            "name": odds_label,
            "value": f"`{float(odd1):.2f}` / `{float(odd2):.2f}`",
            "inline": True,
        })

    # Field 3 : pari IA
    if bets:
        bet = bets[0]  # le 1er = le plus important
        is_model_pick = bet.get("type") == "model_pick" or bet.get("confidence") == "model_only"
        if is_model_pick:
            value = (
                f":sparkles: **{bet.get('selection', '?')}**\n"
                f"@ `{bet.get('odds', 0):.2f}`\n"
                f"Confiance modele : `{bet.get('model_prob', 0):.0f}%`"
            )
        else:
            value = (
                f":dart: **{bet.get('selection', '?')}**\n"
                f"@ `{bet.get('odds', 0):.2f}`\n"
                f"Edge : `+{bet.get('edge_pct', 0):.1f}%`"
            )
        fields.append({
            "name": "Pari IA Varion",
            "value": value,
            "inline": False,
        })
    else:
        fields.append({
            "name": "Pari IA Varion",
            "value": "Aucun pick (modele < seuil de confiance)",
            "inline": False,
        })

    # Field 4 : heure
    fields.append({
        "name": "Heure du match",
        "value": _format_match_time(match.get("start_timestamp_ms")),
        "inline": False,
    })

    embed = {
        "title": title,
        "description": description,
        "color": color,
        "fields": fields,
        "footer": {
            "text": f"Varion AI · {match.get('tour', 'ATP')} · ID {match.get('id', '?')}",
        },
    }
    return embed


def send_daily_picks(matches: list, webhook_url: str = None) -> bool:
    """Envoie les picks du jour sur Discord. Retourne True si OK.

    matches : liste de dict matches (depuis output['matches'] du job)
    webhook_url : optionnel, sinon lit DISCORD_WEBHOOK_URL en env
    """
    url = webhook_url or WEBHOOK_URL
    if not url:
        print("[Discord] DISCORD_WEBHOOK_URL non defini, skip notification")
        return False

    if not matches:
        print("[Discord] Aucun match a envoyer")
        return False

    # Discord supporte max 10 embeds par message. On en a max 5 normalement.
    embeds = [_build_match_embed(m) for m in matches[:10]]

    # Message d'intro avec tag de date
    today = datetime.now(timezone.utc).strftime("%A %d %B %Y")
    intro = (
        f"## :tennis: Varion AI · Picks tennis du jour\n"
        f"-# {len(matches)} match{'s' if len(matches) > 1 else ''} selectionne{'s' if len(matches) > 1 else ''} chronologiquement"
    )

    payload = {
        "username": "Varion AI",
        "avatar_url": "https://i.imgur.com/yvLqYtL.png",  # placeholder, a remplacer si tu veux
        "content": intro,
        "embeds": embeds,
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                # Cloudflare devant Discord rejette les requetes sans User-Agent
                "User-Agent": "Varion-AI/1.0 (+https://varion.ai)",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status in (200, 204):
                print(f"[Discord] Picks envoyes : {len(embeds)} embed(s)")
                return True
            print(f"[Discord] Reponse inattendue : {resp.status}")
            return False
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8")[:200]
        except Exception:
            pass
        print(f"[Discord] HTTPError {e.code} : {body}")
        return False
    except Exception as e:
        print(f"[Discord] Erreur envoi : {e}")
        return False


# CLI rapide pour tester
if __name__ == "__main__":
    # Test avec un match factice
    test_match = {
        "id": "T_TEST",
        "tour": "ATP",
        "tournament": "Madrid Open",
        "tournament_type": "Masters 1000",
        "surface": "clay",
        "format": "BO3",
        "start_timestamp_ms": int((datetime.now(timezone.utc).timestamp() + 4 * 3600) * 1000),
        "player_a": {"name": "Carlos Alcaraz", "country": "ESP"},
        "player_b": {"name": "Jannik Sinner", "country": "ITA"},
        "predictions": {"winner": {"prob_a": 58, "prob_b": 42}},
        "odds": {"1": 1.85, "2": 2.05, "_source": "estimated"},
        "value_bets": [{
            "market": "Vainqueur Carlos Alcaraz",
            "selection": "Carlos Alcaraz",
            "odds": 1.85,
            "model_prob": 58,
            "edge_pct": 0,
            "confidence": "model_only",
            "type": "model_pick",
        }],
    }
    send_daily_picks([test_match])
