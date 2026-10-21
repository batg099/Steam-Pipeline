-- Les actualités, nettoyées : une ligne par article, sans doublons

with jeux as (
    select unnest(results) as jeu
    from {{ source('raw', 'raw_news') }}
),

articles as (
    select jeu.appid as appid, unnest(jeu.reponse.appnews.newsitems) as article
    from jeux
)

select distinct
    article.gid                 as news_id,
    appid,
    to_timestamp(article.date)  as published_at,
    article.title               as title
from articles
