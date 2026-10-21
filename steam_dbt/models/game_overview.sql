{{ config(materialized="table") }}  -- résultat final : enregistré en vraie table

-- Synthèse : une ligne par jeu

with players as (
    select
        appid,
        arg_max(player_count, collected_at)  as current_players,
        max(player_count)                    as peak_players
    from {{ ref('stg_players') }}
    group by appid
),

news as (
    select
        appid,
        max(published_at)  as last_news_at
    from {{ ref('stg_news') }}
    group by appid
)

select
    players.appid,
    players.current_players,
    players.peak_players,
    news.last_news_at,
    current_date - cast(news.last_news_at as date)  as days_since_last_news
from players
left join news on players.appid = news.appid
