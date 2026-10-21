# 🎮 Steam Data Pipeline

Pipeline de données qui collecte automatiquement, **toutes les heures**, le nombre de joueurs
connectés sur 10 jeux Steam populaires, ainsi que leurs actualités officielles (mises à jour, patchs).

**Question étudiée :** est-ce qu'une mise à jour fait revenir les joueurs sur un jeu ?

## Architecture

```
API Steam ──► collect.py ──► fichiers JSON ──► load.py ──► DuckDB ──► dbt ──► game_overview
              (Python)       (data/)                     (tables brutes)   (tables propres)

Le tout est lancé toutes les heures par GitHub Actions (en continu)
ou par Airflow (en local, avec Docker).
```

| Étape | Fichier | Rôle |
|---|---|---|
| Collecte | `collect.py` | Appelle l'API Steam et sauvegarde les réponses brutes en JSON |
| Chargement | `load.py` | Charge tous les fichiers JSON dans DuckDB (`raw_players`, `raw_news`) |
| Transformation | `steam_dbt/` | Nettoie les données et construit les tables d'analyse, avec des tests |
| Automatisation | `.github/workflows/pipeline.yml` | Lance tout le pipeline toutes les heures sur GitHub |
| Orchestration | `dags/steam_pipeline.py` | DAG Airflow : même pipeline, avec relances automatiques et suivi |

## Les tables

| Table | Contenu |
|---|---|
| `stg_players` | Une ligne par jeu et par collecte : nombre de joueurs connectés |
| `stg_news` | Une ligne par actualité officielle (sans doublons) |
| `game_overview` | Une ligne par jeu : joueurs actuels, pic observé, date de la dernière actualité |

## Sources de données

API publique de Steam, sans clé :
- `ISteamUserStats/GetNumberOfCurrentPlayers` : nombre de joueurs connectés
- `ISteamNews/GetNewsForApp` : actualités officielles d'un jeu

## Stack

Python · requests · DuckDB · SQL · dbt · GitHub Actions · Airflow · Docker

## Lancer le projet en local

```bash
pip install -r requirements.txt

python collect.py players
python collect.py news
python load.py
dbt build --project-dir steam_dbt --profiles-dir steam_dbt
```

## Lancer avec Airflow (Docker)

```bash
docker compose up --build
```

Puis ouvrir http://localhost:8080 et activer le DAG `steam_pipeline`.

Le DAG enchaîne les tâches dans cet ordre :

```
collect_players ─┐
                 ├──► load ──► dbt_build
collect_news ────┘
```

Les deux collectes tournent en parallèle. En cas d'échec, chaque tâche est relancée 2 fois.

## Choix techniques

- **Garder la donnée brute** : les réponses de l'API sont sauvegardées telles quelles, pour pouvoir tout recalculer.
- **ELT** : on charge d'abord les données brutes, puis on les transforme en SQL avec dbt.
- **Base recréée à chaque exécution** à partir des fichiers JSON : pas de doublons, et rien à gérer.
- **GitHub Actions pour la collecte en continu** : gratuit et toujours disponible, sans serveur à gérer.
- **Airflow pour l'orchestration** : dépendances entre tâches, relances automatiques et suivi visuel. Il tourne en local avec Docker, puisqu'un serveur permanent serait payant.
- **dbt dans un environnement Python séparé** dans l'image Airflow, pour éviter les conflits de versions entre les deux outils.

## Prochaines étapes

- [ ] Comparer le nombre de joueurs avant et après chaque mise à jour
- [ ] Ajouter un dashboard
- [ ] Déployer Airflow sur un serveur pour remplacer GitHub Actions
