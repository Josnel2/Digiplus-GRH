import os
import requests
from django.conf import settings
from .rag_utils import search_context_for_query

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

def call_deepseek_api(messages, temperature=0.7):
    """
    Fonction utilitaire pour appeler l'API DeepSeek via requests.
    """
    api_key = getattr(settings, 'DEEPSEEK_API_URL', None)
    if not api_key:
        raise ValueError("DEEPSEEK_API_URL n'est pas configuré dans settings.py.")

    model_name = getattr(settings, 'DEEPSEEK_DEFAULT_MODEL', 'deepseek-chat')

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature
    }

    response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    
    data = response.json()
    return data['choices'][0]['message']['content']


def ask_deepseek_chatbot(user, question):
    """
    IA1 / IA4 : Chatbot RH avec contexte utilisateur et gestion de l'escalade
    """
    context = ""
    if user:
        department_name = user.department.name if getattr(user, 'department', None) else "Non assigné"
        role = user.role if hasattr(user, 'role') else "Employé"
        context = f"L'employé(e) qui te parle s'appelle {user.get_full_name() or user.email}. Son département est '{department_name}' et son rôle est '{role}'."

    # Recherche du contexte RAG
    try:
        context_docs = search_context_for_query(question, k=3)
    except Exception as e:
        context_docs = "" # On ignore si FAISS n'est pas encore initialisé
        print(f"Erreur RAG: {e}")

    rag_instruction = ""
    if context_docs:
        rag_instruction = f"""\nVoici des extraits de documents officiels de l'entreprise qui pourraient être pertinents pour répondre à la question :
{context_docs}
BASE TA RÉPONSE SUR CES DOCUMENTS SI PERTINENT. Si les documents ne contiennent pas la réponse, utilise tes connaissances générales ou transfère à un humain si c'est très spécifique.
"""

    system_prompt = f"""Tu es l'assistant IA RH officiel du MINSANTE (Ministère de la Santé Publique du Cameroun), intégré à la plateforme MINSANTE-RH.
Ton rôle est d'aider les employés avec leurs questions administratives, de congés, de règles internes, etc.
Tu dois répondre de manière professionnelle, claire et concise.
Voici les informations sur l'utilisateur actuel : {context}
{rag_instruction}
RÈGLE ABSOLUE (ESCALADE) : 
Si la question est hors sujet (ex: recette de cuisine, politique internationale) ou si tu n'as pas la réponse exacte concernant les RH ou le MINSANTE, tu DOIS répondre EXACTEMENT et UNIQUEMENT par ce mot-clé : __ESCALADE_HUMAIN__
Ne donne aucune autre explication si tu déclenches l'escalade.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]

    try:
        reply = call_deepseek_api(messages)
        if "__ESCALADE_HUMAIN__" in reply:
            return {
                "status": "escalated",
                "message": "Je ne peux pas répondre à cette question. Je vous transfère vers un agent RH humain pour vous assister."
            }
        return {
            "status": "success",
            "message": reply
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erreur de communication avec l'IA: {str(e)}"
        }


def analyze_performance_trends(users_data):
    """
    IA2 : Moteur IA - Analyse des tendances de performance à partir d'un dict/liste de données anonymisées.
    """
    system_prompt = """Tu es un expert RH Data Analyst.
Je vais te fournir des données agrégées sur les employés (présences, retards, congés).
Rédige un court résumé analytique (3 paragraphes maximum) identifiant les tendances de performance, les risques (ex: absentéisme) et des recommandations globales pour la direction.
"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Voici les données : {str(users_data)}"}
    ]

    try:
        reply = call_deepseek_api(messages, temperature=0.5)
        return {"status": "success", "analysis": reply}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def recommend_formations(user_profile_data):
    """
    IA3 : Moteur IA - Recommandation de formations basées sur le profil de l'utilisateur.
    """
    system_prompt = """Tu es un conseiller d'orientation et de carrière RH.
Je vais te donner le profil d'un membre du personnel médical/administratif du MINSANTE.
Génère 3 à 5 suggestions précises de parcours ou de formations continues adaptées pour faire évoluer sa carrière ou améliorer ses compétences.
Réponds de façon structurée (liste à puces) et sois très concret.
"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Voici le profil : {str(user_profile_data)}"}
    ]

    try:
        reply = call_deepseek_api(messages)
        return {"status": "success", "recommendations": reply}
    except Exception as e:
        return {"status": "error", "message": str(e)}
