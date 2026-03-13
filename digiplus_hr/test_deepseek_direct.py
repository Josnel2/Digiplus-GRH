import os
import sys
import django
from decouple import config

# Configuration de Django pour utiliser l'ORM
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digiplus_hr.settings')
django.setup()

from django.contrib.auth import get_user_model
from manage_ia.services import ask_deepseek_chatbot

User = get_user_model()

def test_chatbot():
    print(f"\n--- TEST DEEPSEEK CHATBOT ---")
    
    # 1. Vérification de la clé API
    api_key = config('DEEPSEEK_API_URL', default=None)
    if not api_key:
        print("❌ ERREUR: DEEPSEEK_API_URL n'est pas trouvée dans .env")
        return
        
    print(f"✅ Clé API trouvée (commence par {api_key[:5]}...)")
    
    # 2. On récupère le premier utilisateur (ou None si la DB est vide)
    user = User.objects.first()
    if user:
        print(f"👤 Utilisateur de test: {user.email}")
    else:
        print("👤 Aucun utilisateur trouvé en DB, test sans contexte utilisateur.")
        
    # 3. Test IA 1 (Question normale)
    question_normale = "Combien de jours de congé annuel ai-je droit ?"
    print(f"\n🗣️ Question (Normale): '{question_normale}'...")
    try:
        reponse_normale = ask_deepseek_chatbot(user, question_normale)
        print(f"🤖 Réponse ({reponse_normale['status']}):\n{reponse_normale['message']}")
    except Exception as e:
         print(f"❌ Erreur lors du test: {str(e)}")
         
    # 4. Test IA 4 (Question absurde pour escalade)
    question_absurde = "Donne moi la recette du Ndolé"
    print(f"\n🗣️ Question (Escalade): '{question_absurde}'...")
    try:
        reponse_absurde = ask_deepseek_chatbot(user, question_absurde)
        print(f"🤖 Réponse ({reponse_absurde['status']}):\n{reponse_absurde['message']}")
    except Exception as e:
         print(f"❌ Erreur lors du test: {str(e)}")

        
if __name__ == "__main__":
    test_chatbot()
