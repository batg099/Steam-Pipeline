"""DAG Airflow : lance le pipeline Steam toutes les heures.

Ordre des tâches :

    collect_players ─┐
                     ├──► load ──► dbt_build
    collect_news ────┘

Les deux collectes tournent en parallèle, puis le chargement attend qu'elles
soient toutes les deux terminées, et dbt attend le chargement.
"""
from datetime import datetime, timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

# Dossier du projet dans le conteneur Docker (voir docker-compose.yml)
PROJET = "/opt/airflow/project"

# dbt est installé dans un environnement Python à part (voir Dockerfile)
DBT = "/home/airflow/dbt_venv/bin/dbt"

with DAG(
    dag_id="steam_pipeline",
    description="Collecte Steam -> DuckDB -> dbt",
    schedule="@hourly",                    # toutes les heures
    start_date=datetime(2026, 10, 1),
    catchup=False,                         # ne pas rattraper les heures passées
    default_args={
        "retries": 2,                      # en cas d'échec, réessayer 2 fois...
        "retry_delay": timedelta(minutes=5),  # ...en attendant 5 minutes
    },
    tags=["steam"],
) as dag:

    collect_players = BashOperator(
        task_id="collect_players",
        bash_command="python collect.py players",
        cwd=PROJET,
    )

    collect_news = BashOperator(
        task_id="collect_news",
        bash_command="python collect.py news",
        cwd=PROJET,
    )

    load = BashOperator(
        task_id="load",
        bash_command="python load.py",
        cwd=PROJET,
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=f"{DBT} build --project-dir steam_dbt --profiles-dir steam_dbt",
        cwd=PROJET,
    )

    # L'ordre d'exécution
    [collect_players, collect_news] >> load >> dbt_build
