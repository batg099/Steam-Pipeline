"""Les 3 agents de l'assistant : l'agent SQL, le vérificateur et l'analyste.

Fonctionnement :
    question -> agent SQL -> exécution sur DuckDB -> vérificateur
             -> (si à corriger : retour à l'agent SQL, 3 essais max)
             -> analyste -> réponse en français
"""
from typing import Literal

import duckdb
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

BASE = "data/steam.duckdb"
MODELE = "gemini-3.8-flash"   # identifiant exact du modèle, à vérifier dans AI Studio
LIMITE_LIGNES = 100
ESSAIS_MAX = 3

DESCRIPTION_TABLES = """
Base de données DuckDB sur l'activité de 10 jeux Steam.

Table games : la liste des jeux suivis.
- appid (integer) : identifiant du jeu sur Steam
- game_name (varchar) : nom du jeu, par exemple 'Counter-Strike 2'

Table stg_players : le nombre de joueurs connectés, une ligne par jeu et par collecte.
- collected_at (timestamp, heure UTC) : moment de la collecte
- appid (integer) : identifiant du jeu
- player_count (integer) : nombre de joueurs connectés à ce moment-là
Il y a environ 4 à 6 collectes par jour, à des heures irrégulières.

Table stg_news : les actualités officielles des jeux, une ligne par actualité.
- news_id (varchar) : identifiant de l'actualité
- appid (integer) : identifiant du jeu
- published_at (timestamp with time zone) : date de publication
- title (varchar) : titre de l'actualité

Table game_overview : une synthèse, une ligne par jeu.
- appid (integer) : identifiant du jeu
- current_players (integer) : nombre de joueurs à la collecte la plus récente
- peak_players (integer) : nombre maximum de joueurs observé
- last_news_at (timestamp with time zone) : date de la dernière actualité
- days_since_last_news (integer) : nombre de jours depuis la dernière actualité

Pour retrouver un jeu par son nom, faire une jointure avec la table games sur appid.
"""


# --- Exécution sécurisée des requêtes ---------------------------------------

def nettoyer(requete):
    """Retire les balises ```sql que le LLM ajoute parfois autour de la requête."""
    return requete.replace("```sql", "").replace("```", "").strip()


def verifier_securite(requete):
    """Renvoie un message si la requête est interdite, sinon None."""
    debut = requete.lower()
    if not (debut.startswith("select") or debut.startswith("with")):
        return "Seules les requêtes de lecture (select) sont autorisées."
    if ";" in requete:
        return "Une seule requête à la fois est autorisée."
    return None


def executer_sql(requete):
    """Exécute une requête en lecture seule, sans accès aux fichiers, 100 lignes max."""
    requete = requete.strip().rstrip(";").strip()

    probleme = verifier_securite(requete)
    if probleme:
        raise ValueError(probleme)

    con = duckdb.connect(BASE, read_only=True, config={"enable_external_access": False})
    try:
        return con.sql(f"select * from ({requete}) limit {LIMITE_LIGNES}").df()
    finally:
        con.close()


# --- Les agents --------------------------------------------------------------

class Verification(BaseModel):
    statut: Literal["ok", "a_corriger", "impossible"]
    explication: str


PROMPT_SQL = ChatPromptTemplate.from_template("""
Tu es un expert SQL. Écris une requête DuckDB qui répond à la question.

{description}

Règles :
- Réponds uniquement avec la requête SQL, sans explication.
- Utilise uniquement les tables et les colonnes décrites ci-dessus.
- Si la question demande un classement ou un maximum, renvoie aussi la valeur concernée.

Tentative précédente : {retour}

Question : {question}
""")

PROMPT_VERIFICATEUR = ChatPromptTemplate.from_template("""
Tu vérifies le travail d'un agent SQL.

{description}

Question : {question}
Requête SQL : {requete}
Résultat (ou erreur) :
{resultat}

Choisis un statut :
- "ok" si le résultat répond correctement et complètement à la question, et qu'il contient les valeurs chiffrées qui justifient la réponse ;
- "a_corriger" si la requête a échoué, ou si le résultat ne répond pas bien à la question (incomplet, mauvaise table, mauvais filtre...) ;
- "impossible" si la base ne contient pas l'information nécessaire pour répondre.

Dans l'explication, décris le problème en une ou deux phrases.
""")

PROMPT_ANALYSTE = ChatPromptTemplate.from_template("""
Tu es un analyste de données sur les jeux Steam. Réponds à la question en français, en 1 à 3 phrases.

Question : {question}
Résultat de la requête :
{resultat}

Verdict du vérificateur : {statut} — {explication}
Dernière collecte de données : {derniere_collecte} (heure UTC)

Règles :
- Appuie-toi uniquement sur le résultat, n'invente aucun chiffre.
- Si le verdict est "impossible", explique que les données ne permettent pas de répondre, et pourquoi.
- Si le verdict est "a_corriger", dis que tu n'as pas pu obtenir de réponse fiable.
- Si la question porte sur la situation actuelle, précise que les chiffres datent de la dernière collecte.
""")


def creer_agents(cle_api):
    """Crée les 3 agents, qui utilisent tous le même modèle Gemini."""
    llm = ChatGoogleGenerativeAI(model=MODELE, google_api_key=cle_api, max_retries=2, timeout=120)
    return {
        "sql": PROMPT_SQL | llm | StrOutputParser(),
        "verificateur": PROMPT_VERIFICATEUR | llm.with_structured_output(Verification),
        "analyste": PROMPT_ANALYSTE | llm | StrOutputParser(),
    }


# --- L'assistant complet -----------------------------------------------------

def repondre(question, agents, afficher=print):
    """Fait travailler les 3 agents. `afficher` permet de suivre les étapes."""
    retour = "aucune."
    essais = []

    for essai in range(1, ESSAIS_MAX + 1):
        # 1. L'agent SQL écrit la requête
        afficher(f"Essai {essai} : l'agent SQL écrit la requête...")
        requete = nettoyer(agents["sql"].invoke({
            "description": DESCRIPTION_TABLES, "question": question, "retour": retour,
        }))

        # 2. On l'exécute
        tableau = None
        try:
            tableau = executer_sql(requete)
            resultat = tableau.to_string(index=False)
        except Exception as erreur:
            resultat = "ERREUR : " + str(erreur)

        # 3. Le vérificateur juge le résultat
        afficher(f"Essai {essai} : le vérificateur contrôle le résultat...")
        verif = agents["verificateur"].invoke({
            "description": DESCRIPTION_TABLES, "question": question,
            "requete": requete, "resultat": resultat,
        })
        afficher(f"Essai {essai} : {verif.statut} — {verif.explication}")
        essais.append({"requete": requete, "tableau": tableau, "statut": verif.statut,
                       "explication": verif.explication})

        # 4. On s'arrête si c'est bon, ou si c'est impossible
        if verif.statut in ("ok", "impossible"):
            break
        retour = f"\n{requete}\nRésultat : {resultat}\nProblème signalé : {verif.explication}"

    # 5. L'analyste rédige la réponse
    afficher("L'analyste rédige la réponse...")
    derniere_collecte = executer_sql("select max(collected_at) as t from stg_players")["t"][0]
    reponse = agents["analyste"].invoke({
        "question": question, "resultat": resultat,
        "statut": verif.statut, "explication": verif.explication,
        "derniere_collecte": derniere_collecte,
    })
    return {"reponse": reponse, "essais": essais}
