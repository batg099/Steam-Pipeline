"""Charge tous les fichiers JSON dans la base DuckDB (tables raw_players et raw_news).

La base est recréée à chaque fois à partir des fichiers : on peut relancer
ce script autant de fois qu'on veut, sans créer de doublons.
"""
import duckdb

con = duckdb.connect("data/steam.duckdb")

con.execute("""
    create or replace table raw_players as
    select * from read_json('data/players/*.json', filename = true, union_by_name = true)
""")

con.execute("""
    create or replace table raw_news as
    select * from read_json('data/news/*.json', filename = true, union_by_name = true)
""")

print("raw_players :", con.sql("select count(*) from raw_players").fetchone()[0], "fichiers chargés")
print("raw_news    :", con.sql("select count(*) from raw_news").fetchone()[0], "fichiers chargés")

con.close()
