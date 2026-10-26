"""Collecte les données de l'API Steam et les sauvegarde en fichiers JSON.

Usage :
    python collect.py players   # nombre de joueurs connectés
    python collect.py news      # actualités officielles
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

JEUX = {
    730: "Counter-Strike 2",
    570: "Dota 2",
    578080: "PUBG: BATTLEGROUNDS",
    1172470: "Apex Legends",
    271590: "Grand Theft Auto V",
    252490: "Rust",
    440: "Team Fortress 2",
    1086940: "Baldur's Gate 3",
    1245620: "ELDEN RING",
    2767030: "Marvel Rivals",
}

URL_PLAYERS = "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
URL_NEWS = "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/"


def appeler_api(url, params):
    """Appelle l'API. En cas d'erreur, réessaie jusqu'à 3 fois, puis renvoie None."""
    for essai in range(1, 4):
        try:
            reponse = requests.get(url, params=params, timeout=30)
            reponse.raise_for_status()
            return reponse.json()
        except requests.RequestException as erreur:
            print(f"Essai {essai}/3 raté pour le jeu {params['appid']} : {erreur}")
            time.sleep(10)
    return None


def collecter_joueurs():
    resultats = []
    for appid in JEUX:
        data = appeler_api(URL_PLAYERS, {"appid": appid})
        if data is not None:
            resultats.append({"appid": appid, "reponse": data})
    return resultats


def collecter_actualites():
    resultats = []
    for appid in JEUX:
        params = {
            "appid": appid,
            "count": 20,
            "feeds": "steam_community_announcements",
            "maxlength": 300,
        }
        data = appeler_api(URL_NEWS, params)
        if data is not None:
            resultats.append({"appid": appid, "reponse": data})
    return resultats


def sauvegarder(source, resultats):
    if not resultats:
        print("Aucune donnée récupérée : rien à sauvegarder.")
        sys.exit(1)

    maintenant = datetime.now(timezone.utc)
    dossier = Path("data") / source
    dossier.mkdir(parents=True, exist_ok=True)

    chemin = dossier / (source + "_" + maintenant.strftime("%Y%m%dT%H%M%SZ") + ".json")
    contenu = {"collected_at": maintenant.isoformat(), "results": resultats}
    chemin.write_text(json.dumps(contenu))
    print("Sauvegardé :", chemin)


if __name__ == "__main__":
    source = sys.argv[1]

    if source == "players":
        sauvegarder("players", collecter_joueurs())
    elif source == "news":
        sauvegarder("news", collecter_actualites())
    else:
        print("Source inconnue :", source)
        sys.exit(1)
