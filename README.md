# Steam Data Pipeline

Pipeline that collects the number of players and the news of 10 Steam games every hour.

Goal: find out whether game updates bring players back.

## Steps

1. `collect.py`: fetches data from the Steam API and saves it as JSON
2. `load.py`: loads the JSON files into DuckDB
3. `steam_dbt/`: cleans the data and builds a summary table per game
4. GitHub Actions: runs everything automatically every hour

An Airflow DAG (`dags/`) can also run the pipeline locally with Docker.

## Stack

Python, DuckDB, SQL, dbt, GitHub Actions, Airflow, Docker

## Run the project

```bash
pip install -r requirements.txt
python collect.py players
python collect.py news
python load.py
dbt build --project-dir steam_dbt --profiles-dir steam_dbt
```

With Airflow:

```bash
docker compose up --build
```

Then open http://localhost:8080
