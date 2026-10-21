-- Les joueurs, nettoyés : une ligne par jeu et par collecte

with exploded as (
    select collected_at, unnest(results) as jeu
    from {{ source('raw', 'raw_players') }}
)

select
    collected_at,
    jeu.appid                          as appid,
    jeu.reponse.response.player_count  as player_count
from exploded
where jeu.reponse.response.result = 1   -- on garde seulement les réponses valides
