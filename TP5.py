import streamlit as st
import requests
import json
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Config
API_URL = "http://localhost:5000" 

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://sdv_user:SDV2025@cluster0.t2ptc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

##################################### Fonctions #####################################

def get_client_personal_data(client_id):
    """
    Récupère les données personnelles du client depuis MongoDB
    """
    try:
        # Connexion
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client['default_risk']
        collection = db['users_data']

        # Recherche du client
        result = collection.find_one({"SK_CURR_ID": int(client_id)})

        # Fermeture propre
        client.close()

        if result:
            # Sélectionne les champs utiles (personnalisables)
            personal_data = {
                "FirstName": result.get("FirstName", ""),
                "LastName": result.get("LastName", ""),
                "PhotoURL": result.get("PhotoURL", "")
            }
            return personal_data
        else:
            return None

    except ConnectionFailure as e:
        print(f"[MongoDB] Connexion échouée : {e}")
        return None
    except Exception as e:
        print(f"[MongoDB] Erreur : {e}")
        return None

import requests

def predict_default_risk(client_id):
    """
    Appelle l'API Flask pour obtenir la prédiction de risque de défaut
    et prépare les données pour l'affichage.
    
    Parameters:
        client_id (str): Identifiant unique du client
        
    Returns:
        dict: Dictionnaire contenant les résultats formatés avec les clés suivantes :
            - client_info (dict): Informations générales du client
            - risk_score (float): Score de risque en pourcentage (0-100)
            - risk_category (str): Catégorie de risque (Faible, Moyen, Élevé)
            - impact_factors (list): Facteurs influençant le score de risque
            - recommendation (str): Recommandation d'action
            
    Raises:
        Exception: En cas d'erreur de connexion ou de réponse API
    """

    try:
        # Appel GET à l'API avec le paramètre client_id
        response = requests.get(f"{API_URL}/predict_default", params={"client_id": client_id})
        
        if response.status_code != 200:
            raise Exception(f"Erreur API : {response.status_code} - {response.text}")
        
        data = response.json()
        
        # Extraction des infos client
        client_info = data.get("client_info", {})
        
        # Extraction prédiction
        pred = data.get("prediction", {})
        risk_score = pred.get("risk_score", 0) * 100  # en %
        
        # Catégorisation simple du risque selon score
        if risk_score < 30:
            risk_category = "Faible"
        elif risk_score < 70:
            risk_category = "Moyen"
        else:
            risk_category = "Élevé"
        
        # Facteurs d'impact (exemple, peut dépendre du format exact API)
        impact_factors = pred.get("impact_factors", [])
        
        # Recommandation
        reco = data.get("recommendation", {})
        recommendation = reco.get("decision", "Pas de recommandation disponible")
        
        # Retour structuré
        return {
            "client_info": client_info,
            "risk_score": round(risk_score, 2),
            "risk_category": risk_category,
            "impact_factors": impact_factors,
            "recommendation": recommendation
        }
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"Erreur de connexion à l'API : {e}")


##################################### Fin des Fonctions #############################

st.set_page_config(
    page_title="Titre de la page | Risk Banking",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Tableau de bord - Prédiction du Risque Client")

# --- Barre latérale stylisée ---
st.sidebar.image("https://png.pngtree.com/png-vector/20220624/ourmid/pngtree-bank-icon-blue-logo-simple-png-image_5375462.png", width=80)
st.sidebar.markdown("## Risk Banking")
st.sidebar.markdown("**Analyses & Intelligence Décisionnelle**")
st.sidebar.markdown("---")

st.sidebar.markdown("### 🎯 THÉMATIQUE D'ANALYSE")

analysis_display = {
    "🙂💀 Âge client et défaut": "1",
    "💰💳 Ratio crédit/revenu": "2",
    "💼🧾 Type de revenu": "3",
    "📘📊 Ancienneté d'emploi": "4",
    "📈📉 Prédiction d'un client": "5",
    "📊📈 Exploration des données": "6",
    "📄📆 Demande de crédit": "7",
    "🏠📄 Type de contrat & propriété": "8",
    "👨‍👩‍👧🙂 Enfants & statut familial": "9",
    "📅📆 Jour de demande & saisonnalité": "10"
}

selected_label = st.sidebar.radio(
    label="",
    options=list(analysis_display.keys()),
    index=0
)

analysis_type = analysis_display[selected_label]

# ---------- MODE PRÉDICTION ----------
if selected_label == "📈📉 Prédiction d'un client":
    st.subheader("📌 Prédiction du risque de défaut")
    client_id = st.text_input("Entrez l'ID du client :", value="120194")

    if st.button("Lancer la prédiction"):
        with st.spinner("Appel à l'API en cours..."):
            try:
                response = requests.get(f"{API_URL}/predict_default", params={"client_id": client_id})
                if response.status_code == 200:
                    result = response.json()
                    st.success("✅ Prédiction reçue avec succès.")

                    st.markdown("### 👤 Informations client")
                    st.json(result["client_info"])

                    st.markdown("### 🧠 Prédiction")
                    pred = result["prediction"]
                    st.metric(label="Score de risque (%)", value=round(pred["risk_score"] * 100, 2))
                    st.write("Défaut prédit :", "Oui" if pred["predicted_default"] else "Non")

                    st.markdown("### 💡 Recommandation")
                    reco = result.get("recommendation", {})
                    st.write(f"**Décision** : {reco.get('decision', 'N/A')}")
                    st.write(f"**Explication** : {reco.get('explanation', '')}")
                    st.write("**Plan d'action :**")
                    st.markdown("\n".join([f"- {item}" for item in reco.get("action_plan", [])]))

                    # Métadonnées
                    meta = result.get("metadata", {})
                    with st.expander("🗂️ Métadonnées de l'analyse"):
                        st.json(meta)

                    # Feedback utilisateur
                    st.markdown("---")
                    st.markdown("### ✉️ Donner un retour")
                    feedback_text = st.text_area("Votre commentaire")
                    feedback_type = st.radio("Ce retour est :", ["Positif", "Négatif"])
                    if st.button("Envoyer le feedback"):
                        payload = {
                            "message": feedback_text,
                            "is_positive": feedback_type == "Positif",
                            "custom_dimensions": {"client_id": client_id}
                        }
                        fb_resp = requests.post(f"{API_URL}/feedback", json=payload)
                        if fb_resp.status_code == 200:
                            st.success("Merci pour votre retour !")
                        else:
                            st.error("Erreur lors de l'envoi du feedback.")

                else:
                    st.error(f"Erreur API : {response.status_code} - {response.text}")

            except Exception as e:
                st.error(f"Erreur de connexion à l'API : {e}")

elif selected_label == "🙂💀 Âge client et défaut":
    client_id = st.text_input("Entrez l'ID du client :", value="120194")
    personal = get_client_personal_data(client_id)
    if personal:
        st.markdown(f"👤 **{personal['FirstName']} {personal['LastName']}**")
        st.image(personal["PhotoURL"], width=100)
    else:
        st.warning("Aucune donnée personnelle trouvée.")

# ---------- MODE DATAVIZ ----------
elif selected_label == "📊📈 Exploration des données":
    st.subheader("📈 Analyse visuelle depuis Databricks")

    analysis_type = st.selectbox("Type d'analyse", options=[
        ("1", "Taux de défaut par groupe d'âge"),
        ("2", "Ratio crédit/revenu"),
        ("3", "Type de revenu et taux de défaut"),
        ("4", "Ancienneté d'emploi"),
        ("5", "Demandes de crédit"),
        ("6", "Type de contrat & propriété"),
        ("7", "Enfants & statut familial"),
        ("8", "Jour de demande & saisonnalité")
    ], format_func=lambda x: x[1])[0]

    st.markdown("#### Filtres (optionnels)")
    col1, col2, col3 = st.columns(3)
    with col1:
        min_credit = st.number_input("Montant crédit min", min_value=0, value=0)
    with col2:
        max_credit = st.number_input("Montant crédit max", min_value=0, value=0)
    with col3:
        min_income = st.number_input("Revenu minimum", min_value=0, value=0)

    job_id = st.text_input("Job ID (obligatoire)", value="dummy_job")

    if st.button("Générer la visualisation"):
        with st.spinner("Chargement de la visualisation..."):
            params = {
                "job_id": job_id,
                "analysis_type": analysis_type,
                "min_credit": min_credit or "",
                "max_credit": max_credit or "",
                "min_income": min_income or ""
            }
            try:
                viz_response = requests.get(f"{API_URL}/get_dataviz", params=params)
                if viz_response.status_code == 200:
                    st.components.v1.html(viz_response.text, height=750, scrolling=True)
                else:
                    st.error(f"Erreur API : {viz_response.status_code}")
            except Exception as e:
                st.error(f"Erreur de connexion à l'API : {e}")

elif analysis_type in ["1", "2", "3", "4"]:
    st.subheader(f"📊 Analyse : {selected_label}")

    job_id = st.text_input("Job ID (obligatoire)", value="dummy_job")
    if st.button("Générer la visualisation"):
        with st.spinner("Chargement..."):
            params = {
                "job_id": job_id,
                "analysis_type": analysis_type,
            }
            try:
                viz_response = requests.get(f"{API_URL}/get_dataviz", params=params)
                if viz_response.status_code == 200:
                    st.components.v1.html(viz_response.text, height=700, scrolling=True)
                else:
                    st.error(f"Erreur API : {viz_response.status_code}")
            except Exception as e:
                st.error(f"Erreur API : {e}")

# Fin du script