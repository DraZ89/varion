#!/usr/bin/env python3
"""
Génère varion_standalone.html avec tout inline (CSS + JS + données + logos SVG).
À exécuter APRÈS download_logos.py.

Usage : python build_standalone.py
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(ROOT, "frontend")
LOGOS_DIR = os.path.join(FRONTEND, "logos")
OUTPUT = os.path.join(ROOT, "varion_standalone.html")

# Ordre d'import des scripts
SCRIPTS = [
    "src/api.js",
    "src/components/Common.js",
    "src/components/MatchCard.js",
    "src/components/MatchDetail.js",
    "src/components/ValueBets.js",
    "src/App.js",
]


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def main():
    # 1. Charger HTML, CSS, données
    html = read(os.path.join(FRONTEND, "index.html"))
    css = read(os.path.join(FRONTEND, "styles.css"))
    data = read(os.path.join(FRONTEND, "data.json"))

    # 2. Charger les SVG (si présents)
    logos = {}
    if os.path.isdir(LOGOS_DIR):
        for fname in os.listdir(LOGOS_DIR):
            if fname.endswith(".svg"):
                team_id = fname[:-4]
                with open(os.path.join(LOGOS_DIR, fname), encoding="utf-8") as f:
                    logos[team_id] = f.read()

    if logos:
        print(f"  ✓ {len(logos)} logos SVG inline-és")
    else:
        print("  ⚠️  Aucun logo trouvé dans frontend/logos/")
        print("    Lance d'abord : python download_logos.py")

    # 3. Charger les scripts
    scripts = {p: read(os.path.join(FRONTEND, p)) for p in SCRIPTS}

    # 4. Patcher api.js pour utiliser les données inline (pas de fetch)
    scripts["src/api.js"] = scripts["src/api.js"].replace(
        'try {\n    const res = await fetch("./data.json");\n    _staticData = await res.json();\n    return _staticData;\n  } catch (e) {\n    return null;\n  }',
        '_staticData = window.__INLINE_DATA__;\n    return _staticData;',
    )

    # 5. Patcher Common.js pour utiliser les logos inline (pas de fetch)
    common_patched = scripts["src/components/Common.js"].replace(
        '''fetch(`./logos/${team.id}.svg`)
      .then(r => {
        if (!r.ok) throw new Error("404");
        return r.text();
      })
      .then(svg => {
        // Sécurité minimum : retirer les scripts éventuels du SVG
        const clean = svg.replace(/<script[\\s\\S]*?<\\/script>/gi, "");
        window.__LOGO_CACHE[team.id] = clean;
        setSvgContent(clean);
      })
      .catch(() => {
        window.__LOGO_FAILED[team.id] = true;
        setFailed(true);
      });''',
        '''const inline = window.__INLINE_LOGOS && window.__INLINE_LOGOS[team.id];
    if (inline) {
      const clean = inline.replace(/<script[\\s\\S]*?<\\/script>/gi, "");
      window.__LOGO_CACHE[team.id] = clean;
      setSvgContent(clean);
    } else {
      window.__LOGO_FAILED[team.id] = true;
      setFailed(true);
    }'''
    )
    scripts["src/components/Common.js"] = common_patched

    # 6. Inliner CSS
    html = html.replace(
        '<link rel="stylesheet" href="/styles.css" />',
        f"<style>{css}</style>",
    )

    # 7. Construire le bloc de scripts inline
    inline_block = (
        f"<script>window.__INLINE_DATA__ = {data};</script>\n"
        f"<script>window.__INLINE_LOGOS__ = {json.dumps(logos)};\n"
        f"window.__INLINE_LOGOS = window.__INLINE_LOGOS__;</script>\n"
        f'<script type="text/babel" data-presets="react">\n'
    )
    for p in SCRIPTS:
        inline_block += scripts[p] + "\n"
    inline_block += "</script>\n"

    # 8. Retirer les imports modulaires et inserer le bloc inline
    html = re.sub(r'<script type="text/babel".*?></script>', "", html, flags=re.DOTALL)
    html = html.replace("</body>", inline_block + "</body>")

    # 9. Écrire le fichier
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(OUTPUT) / 1024
    print(f"\n  ✓ {OUTPUT}  ({size_kb:.1f} KB)")
    print(f"    Ouvre ce fichier dans un navigateur. Aucun serveur nécessaire.")


if __name__ == "__main__":
    main()
