"""Reconstruit la base DuckDB : chargement des JSON (load.py), puis dbt build.

Utilisé par l'application au démarrage. Il tourne dans un processus séparé,
pour que dbt referme bien sa connexion à la base avant que l'application l'ouvre.
"""
import subprocess
import sys

from dbt.cli.main import dbtRunner

subprocess.run([sys.executable, "load.py"], check=True)
resultat = dbtRunner().invoke(["build", "--project-dir", "steam_dbt", "--profiles-dir", "steam_dbt"])
sys.exit(0 if resultat.success else 1)
