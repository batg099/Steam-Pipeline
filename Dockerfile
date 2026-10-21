# Image officielle d'Airflow
FROM apache/airflow:3.3.2

# Bibliothèques utilisées par collect.py et load.py
RUN pip install --no-cache-dir requests==2.34.2 duckdb==1.5.6

# dbt dans un environnement Python séparé, pour éviter les conflits
# de versions avec les bibliothèques d'Airflow
RUN python -m venv /home/airflow/dbt_venv \
    && /home/airflow/dbt_venv/bin/pip install --no-cache-dir dbt-core==1.12.6 dbt-duckdb==1.11.0
