"""
Termine tout seul une publication commencée : pour chaque ville, la
release publiée la plus récente (tag <id>-v<N>) dont le catalogue
villes.json n'a pas encore la version N y est inscrite (fichiers, tailles,
empreintes, date, fiche), l'ancienne entrée gardée comme « precedente ».

Lancé par .github/workflows/catalogue.yml (à chaque release publiée et
toutes les 6 heures). Sans dépendance : bibliothèque standard seulement.
Une release trop récente (moins de 3 minutes) est laissée au kit, qui
écrit lui-même le catalogue juste après avoir publié.
"""

import hashlib
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEPOT = os.environ.get("DEPOT", "leboncash006-max/fresko-donnees")
CATALOGUE = Path(__file__).resolve().parent.parent / "villes.json"
NON_PUBLIES = {"ville.json", "villes.json"}
CHAMPS_FICHE = ("description", "communes", "contour")
DELAI = timedelta(minutes=int(os.environ.get("DELAI_MINUTES", "3")))


def demande(url, accept="application/vnd.github+json"):
    entetes = {"Accept": accept, "User-Agent": "fresko-catalogue"}
    if os.environ.get("GITHUB_TOKEN"):
        entetes["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    return urllib.request.urlopen(urllib.request.Request(url, headers=entetes), timeout=120)


def releases():
    tout, page = [], 1
    while True:
        with demande(f"https://api.github.com/repos/{DEPOT}/releases?per_page=100&page={page}") as r:
            lot = json.load(r)
        tout += lot
        if len(lot) < 100:
            return tout
        page += 1


def contenu(asset):
    with demande(asset["url"], accept="application/octet-stream") as r:
        return r.read()


def empreinte(asset):
    h, taille = hashlib.sha256(), 0
    with demande(asset["url"], accept="application/octet-stream") as r:
        while morceau := r.read(1 << 20):
            h.update(morceau)
            taille += len(morceau)
    return h.hexdigest(), taille


def resume(entree):
    return {k: entree[k] for k in ("version", "date", "fichiers") if k in entree}


def main():
    catalogue = json.loads(CATALOGUE.read_text(encoding="utf-8")) if CATALOGUE.exists() else []
    maintenant = datetime.now(timezone.utc)
    dernieres = {}
    for r in releases():
        m = re.fullmatch(r"(.+)-v(\d+)", r["tag_name"])
        if r["draft"] or r["prerelease"] or not m:
            continue
        noms = {a["name"] for a in r["assets"] if a["state"] == "uploaded"}
        if "graphe_routage.bin" not in noms:
            continue
        id_ville, version = m.group(1), int(m.group(2))
        if version > dernieres.get(id_ville, (0, None))[0]:
            dernieres[id_ville] = (version, r)

    change = False
    for id_ville, (version, r) in sorted(dernieres.items()):
        entree = next((v for v in catalogue if v.get("id") == id_ville), None)
        if entree and entree.get("version", 0) >= version:
            continue
        publiee = datetime.fromisoformat((r["published_at"] or r["created_at"]).replace("Z", "+00:00"))
        if maintenant - publiee < DELAI:
            print(f"{r['tag_name']} : publiée il y a moins de {DELAI}, laissée au kit.")
            continue
        assets = {a["name"]: a for a in r["assets"] if a["state"] == "uploaded"}
        meta = dict(entree or {})
        if "ville.json" in assets:
            meta.update(json.loads(contenu(assets["ville.json"]).decode("utf-8-sig")))
        if not all(k in meta for k in ("nom", "lat", "lon")):
            print(f"{r['tag_name']} : ni ville.json dans la release, ni ville déjà connue : ignorée.")
            continue
        date = None
        if "date.txt" in assets:
            lignes = [l.strip() for l in contenu(assets["date.txt"]).decode("utf-8-sig").splitlines()]
            date = next((l for l in lignes if l), None)
        date = date or meta.get("date") or (publiee + timedelta(hours=2)).strftime("%d/%m/%Y %H:%M")
        fichiers = {}
        for nom, asset in sorted(assets.items()):
            if nom in NON_PUBLIES:
                continue
            sha, taille = empreinte(asset)
            fichiers[nom] = {"url": asset["browser_download_url"], "taille": taille, "sha256": sha}
        nouvelle = {
            "id": id_ville, "nom": meta["nom"], "lat": meta["lat"], "lon": meta["lon"],
            "version": version, "date": date, "fichiers": fichiers,
            **{k: meta[k] for k in CHAMPS_FICHE if meta.get(k)},
        }
        if entree:
            nouvelle["precedente"] = resume(entree)
        catalogue = [v for v in catalogue if v.get("id") != id_ville] + [nouvelle]
        change = True
        print(f"{meta['nom']} : version {version} inscrite au catalogue "
              f"({len(fichiers)} fichiers, données du {date}).")
    if change:
        CATALOGUE.write_text(json.dumps(catalogue, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    else:
        print("Catalogue à jour.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
