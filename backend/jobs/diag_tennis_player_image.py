"""
Test : verifier si l'endpoint /player/{id}/image ou similaire existe sur Matchstat.

Cout : 4 req max (on s'arrete au 1er qui marche).
Usage : python -m jobs.diag_tennis_player_image
"""

import os
import urllib.request
import urllib.error
import json

API_HOST = "tennis-api-atp-wta-itf.p.rapidapi.com"
API_BASE = f"https://{API_HOST}/tennis/v2"


def fetch_raw(url, api_key):
    """Retourne (status, content_type, body_bytes)."""
    req = urllib.request.Request(url, headers={
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": API_HOST,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.headers.get("Content-Type", ""), resp.read()
    except urllib.error.HTTPError as e:
        body = e.read() if e.fp else b""
        return e.code, e.headers.get("Content-Type", ""), body


def main():
    print("=" * 60)
    print("DIAG Tennis - Photo joueur ?")
    print("=" * 60)

    api_key = os.environ.get("RAPIDAPI_KEY")
    if not api_key:
        print("ERREUR : RAPIDAPI_KEY non definie")
        return

    # Player id : Sinner (47275) ou Mannarino (7806)
    pid = 47275

    # On teste plusieurs URLs candidates
    test_urls = [
        f"{API_BASE}/atp/player/{pid}",
        f"{API_BASE}/atp/player/{pid}/image",
        f"{API_BASE}/atp/player/{pid}/photo",
        f"{API_BASE}/atp/player/{pid}/profile",
    ]

    for url in test_urls:
        print(f"\n>>> {url}")
        status, ctype, body = fetch_raw(url, api_key)
        print(f"   Status : {status}")
        print(f"   Content-Type : {ctype}")
        print(f"   Body size : {len(body)} bytes")

        if status == 200:
            if "image" in ctype.lower():
                print(f"   *** BINGO ! C'est une image. ***")
                print(f"   First bytes (hex) : {body[:8].hex()}")
                # Detect format
                if body[:4] == b"\x89PNG":
                    print(f"   Format : PNG")
                elif body[:3] == b"\xff\xd8\xff":
                    print(f"   Format : JPEG")
                elif body[:4] == b"GIF8":
                    print(f"   Format : GIF")
                # On a trouve !
                return
            elif "json" in ctype.lower():
                try:
                    data = json.loads(body.decode("utf-8"))
                    print(f"   JSON keys : {list(data.keys()) if isinstance(data, dict) else type(data).__name__}")
                    print(f"   Body preview : {json.dumps(data, ensure_ascii=False)[:300]}")
                    # Recherche d'URL d'image dans le JSON
                    def find_image_keys(obj, prefix=""):
                        if isinstance(obj, dict):
                            for k, v in obj.items():
                                full = f"{prefix}.{k}" if prefix else k
                                if isinstance(v, str) and ("http" in v or k.lower() in ("image", "photo", "picture", "avatar", "url")):
                                    print(f"      Url-like key : {full} = {v[:120]}")
                                elif isinstance(v, dict):
                                    find_image_keys(v, full)
                    find_image_keys(data)
                except Exception as e:
                    print(f"   JSON parse fail : {e}")
                    print(f"   Body : {body[:200]}")
        elif status == 404:
            print(f"   404 Not Found")
        else:
            print(f"   Body preview : {body[:200].decode('utf-8', errors='replace')}")


if __name__ == "__main__":
    main()
