"""Collecte les données de l'API Steam et les sauvegarde en fichiers JSON.

Usage :
    python collect.py players   # nombre de joueurs connectés
    python collect.py news      # actualités officielles
"""
import json
import sys
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


def collecter_joueurs():
    resultats = []
    for appid in JEUX:
        reponse = requests.get(URL_PLAYERS, params={"appid": appid}, timeout=30)
        resultats.append({"appid": appid, "reponse": reponse.json()})
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
        reponse = requests.get(URL_NEWS, params=params, timeout=30)
        resultats.append({"appid": appid, "reponse": reponse.json()})
    return resultats


def sauvegarder(source, resultats):
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
