"""Interface web de l'assistant Steam.

Lancement en local : streamlit run app.py
La clé Gemini doit être dans .streamlit/secrets.toml (GOOGLE_API_KEY = "...").
"""
import subprocess
import sys

import streamlit as st

from agents import creer_agents, executer_sql, repondre

QUESTIONS_MAX = 10   # par visiteur, pour protéger le quota gratuit de Gemini

EXEMPLES = [
    "Quel jeu a le plus de joueurs en ce moment ?",
    "Quel jeu n'a pas eu d'actualité depuis le plus longtemps ?",
    "Quel est le pic de joueurs observé sur Rust ?",
    "Combien de joueurs a Minecraft ?",
]

st.set_page_config(page_title="Assistant Steam", page_icon="🎮")


@st.cache_resource(show_spinner="Construction de la base de données...")
def preparer_base():
    """Reconstruit la base DuckDB à partir des fichiers JSON du repo (une fois au démarrage)."""
    subprocess.run([sys.executable, "build.py"], check=True)
    return True


@st.cache_resource
def charger_agents(cle_api):
    return creer_agents(cle_api)


def lire_cle_api():
    try:
        return st.secrets["GOOGLE_API_KEY"]
    except Exception:
        return None


# --- Préparation --------------------------------------------------------------

cle_api = lire_cle_api()
if not cle_api:
    st.error("Clé Gemini manquante : ajoute GOOGLE_API_KEY dans les secrets de l'application.")
    st.stop()

preparer_base()
agents = charger_agents(cle_api)

if "historique" not in st.session_state:
    st.session_state.historique = []
if "nb_questions" not in st.session_state:
    st.session_state.nb_questions = 0


# --- Barre latérale -----------------------------------------------------------

with st.sidebar:
    st.header("Comment ça marche")
    st.markdown(
        "1. **L'agent SQL** écrit une requête sur la base.\n"
        "2. **Le vérificateur** contrôle le résultat, et fait corriger la requête si besoin.\n"
        "3. **L'analyste** rédige la réponse."
    )
    derniere = executer_sql("select max(collected_at) as t from stg_players")["t"][0]
    st.caption(f"Dernière collecte des données : {derniere:%d/%m/%Y à %H:%M} (UTC)")

    st.header("Exemples")
    exemple_choisi = None
    for exemple in EXEMPLES:
        if st.button(exemple, use_container_width=True):
            exemple_choisi = exemple


# --- Conversation -------------------------------------------------------------

st.title("🎮 Assistant Steam")
st.caption("Pose une question sur l'activité de 10 jeux Steam : joueurs connectés, pics, actualités.")


def afficher_details(essais):
    with st.expander("Voir le travail des agents"):
        for numero, essai in enumerate(essais, start=1):
            st.markdown(f"**Essai {numero}** : `{essai['statut']}` — {essai['explication']}")
            st.code(essai["requete"], language="sql")
            if essai["tableau"] is not None:
                st.dataframe(essai["tableau"], hide_index=True)


for message in st.session_state.historique:
    with st.chat_message(message["role"]):
        st.markdown(message["texte"])
        if message.get("essais"):
            afficher_details(message["essais"])

question = st.chat_input("Ta question...") or exemple_choisi

if question:
    if st.session_state.nb_questions >= QUESTIONS_MAX:
        st.warning(f"Limite de {QUESTIONS_MAX} questions atteinte pour cette session.")
        st.stop()
    st.session_state.nb_questions += 1

    st.session_state.historique.append({"role": "user", "texte": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.status("Les agents travaillent...", expanded=False) as statut:
                resultat = repondre(question, agents, afficher=statut.write)
                statut.update(label="Terminé", state="complete")
            st.markdown(resultat["reponse"])
            afficher_details(resultat["essais"])
            st.session_state.historique.append(
                {"role": "assistant", "texte": resultat["reponse"], "essais": resultat["essais"]}
            )
        except Exception as erreur:
            message = "Désolé, le service est indisponible pour le moment. Réessaie dans quelques minutes."
            st.error(message)
            st.caption(f"Détail : {erreur}")
            st.session_state.historique.append({"role": "assistant", "texte": message})
