# Steam Data Pipeline

Pipeline qui récupère toutes les heures le nombre de joueurs et les actualités de 10 jeux Steam.

Objectif : voir si une mise à jour fait revenir les joueurs.

## Étapes

1. `collect.py` : récupère les données de l'API Steam et les enregistre en JSON
2. `load.py` : charge les fichiers JSON dans DuckDB
3. `steam_dbt/` : nettoie les données et crée une table de synthèse par jeu
4. GitHub Actions : lance tout automatiquement toutes les heures

Un DAG Airflow (`dags/`) permet aussi de lancer le pipeline en local avec Docker.

## Stack

Python, DuckDB, SQL, dbt, GitHub Actions, Airflow, Docker

## Lancer le projet

```bash
pip install -r requirements.txt
python collect.py players
python collect.py news
python load.py
dbt build --project-dir steam_dbt --profiles-dir steam_dbt
```

Avec Airflow :

```bash
docker compose up --build
```

Puis ouvrir http://localhost:8080
