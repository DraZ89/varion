"""
Matcher de noms de joueurs tennis cross-API.

Gere les variations entre RapidAPI Tennis (souvent "Carlos Alcaraz Garfia")
et The Odds API (souvent "Carlos Alcaraz" ou "C. Alcaraz").

Cas a gerer :
  - Carlos Alcaraz Garfia <-> Carlos Alcaraz : meme joueur (drop suffix)
  - C. Alcaraz <-> Carlos Alcaraz : meme joueur (initiale prenom)
  - Stefanos Tsitsipas <-> Stéfanos Tsitsipás : meme joueur (accents)
  - Hubert Hurkacz <-> H. Hurkacz : meme joueur
  - Felix Auger-Aliassime <-> Felix Auger Aliassime : meme joueur (tirets vs espaces)
"""

import unicodedata
import re


def remove_accents(text: str) -> str:
    """Supprime les accents : Tsitsipás -> Tsitsipas."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalize_player_name(name: str) -> str:
    """Normalise un nom de joueur pour comparaison robuste.

    Etapes :
      1. Trim + lowercase
      2. Supprime accents
      3. Remplace tirets et apostrophes par espaces
      4. Espaces multiples -> espace simple
      5. Supprime ponctuation (sauf espaces et points pour initiales)
    """
    if not name:
        return ""
    s = name.strip().lower()
    s = remove_accents(s)
    s = s.replace("-", " ").replace("'", " ").replace("`", " ")
    s = re.sub(r"[^\w\s\.]", "", s)  # garde lettres, chiffres, espaces, points
    s = re.sub(r"\s+", " ", s).strip()
    return s


def get_last_name(name: str) -> str:
    """Extrait le nom de famille (heuristique).

    Pour "Carlos Alcaraz Garfia" -> "alcaraz garfia" (les 2 derniers tokens)
    Pour "Felix Auger-Aliassime" -> "auger aliassime"
    Pour "C. Alcaraz" -> "alcaraz"
    """
    norm = normalize_player_name(name)
    tokens = [t for t in norm.split() if not t.endswith(".") and len(t) > 1]
    if len(tokens) == 0:
        return ""
    if len(tokens) == 1:
        return tokens[0]
    # 2 derniers tokens = nom de famille (compose si necessaire)
    return " ".join(tokens[-2:])


def get_first_name_initial(name: str) -> str:
    """Extrait l'initiale du prenom.
    "Carlos Alcaraz" -> "c"
    "C. Alcaraz" -> "c"
    "Felix Auger" -> "f"
    """
    norm = normalize_player_name(name)
    tokens = norm.split()
    if not tokens:
        return ""
    first = tokens[0].rstrip(".")
    return first[0] if first else ""


def get_first_name(name: str) -> str:
    """Extrait le prenom complet si dispo.
    "Carlos Alcaraz" -> "carlos"
    "C. Alcaraz" -> "c" (initiale, on garde)
    """
    norm = normalize_player_name(name)
    tokens = norm.split()
    if not tokens:
        return ""
    return tokens[0].rstrip(".")


def match_player_names(name1: str, name2: str) -> bool:
    """Retourne True si name1 et name2 designent le meme joueur.

    Strategie :
      1. Si normalises identiques -> match
      2. Si meme nom de famille (>=2 chars en commun) ET (meme prenom OU meme initiale prenom) -> match
      3. Sinon -> pas match
    """
    if not name1 or not name2:
        return False

    n1 = normalize_player_name(name1)
    n2 = normalize_player_name(name2)

    # Match exact apres normalisation
    if n1 == n2:
        return True

    # Match si l'un contient l'autre (cas suffix : "alcaraz garfia" contient "alcaraz")
    # Mais attention : "ana ivanovic" contient "ana", trop permissif. On exige >=5 chars.
    if len(n1) >= 5 and (n1 in n2 or n2 in n1):
        return True

    # Decomposition prenom / nom de famille
    last1 = get_last_name(name1)
    last2 = get_last_name(name2)
    first1_full = get_first_name(name1)
    first2_full = get_first_name(name2)

    if not last1 or not last2:
        return False

    # Match nom de famille (l'un contient l'autre)
    last_match = (last1 == last2) or (last1 in last2) or (last2 in last1)
    if not last_match:
        return False

    # Match prenom : soit identique, soit initiale matche prenom complet
    # Cas 1 : prenoms identiques (Carlos == Carlos)
    if first1_full == first2_full:
        return True

    # Cas 2 : l'un est une initiale et matche l'autre (c == carlos)
    if len(first1_full) == 1 and first1_full == first2_full[0]:
        return True
    if len(first2_full) == 1 and first2_full == first1_full[0]:
        return True

    return False


# Test direct
if __name__ == "__main__":
    cases = [
        ("Carlos Alcaraz", "Carlos Alcaraz", True),
        ("Carlos Alcaraz Garfia", "Carlos Alcaraz", True),
        ("Stéfanos Tsitsipás", "Stefanos Tsitsipas", True),
        ("C. Alcaraz", "Carlos Alcaraz", True),
        ("Felix Auger-Aliassime", "Felix Auger Aliassime", True),
        ("H. Hurkacz", "Hubert Hurkacz", True),
        # Negatifs
        ("Carlos Alcaraz", "Jannik Sinner", False),
        ("R. Nadal", "R. Federer", False),  # meme initiale mais nom different
    ]
    for n1, n2, expected in cases:
        result = match_player_names(n1, n2)
        ok = "OK" if result == expected else "FAIL"
        print(f"  {ok} : '{n1}' vs '{n2}' -> {result} (expected {expected})")
