#!/usr/bin/env python
"""
Script de test des endpoints de gestion des départements
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/users"

def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def print_response(method, endpoint, status, data):
    print(f"\n📌 {method} {endpoint}")
    print(f"Status: {status}")
    print(f"Response:\n{json.dumps(data, indent=2, ensure_ascii=False)}")

# Step 1: Login
print_header("STEP 1: Authentification")
login_response = requests.post(
    f"{BASE_URL}/login",
    json={"email": "admin@example.com", "password": "admin123"}
)

if login_response.status_code != 200:
    print(f"❌ Login échoué: {login_response.json()}")
    exit(1)

print(f"✓ Login réussi")
tokens = login_response.json()
access_token = tokens.get('access')
print(f"Token obtenu: {access_token[:50]}...")

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# Step 2: Liste des départements
print_header("STEP 2: Liste des Départements (GET)")
response = requests.get(f"{BASE_URL}/departements/", headers=headers)
print_response("GET", "/departements/", response.status_code, response.json())

# Step 3: Créer un nouveau département
print_header("STEP 3: Créer un Département (POST)")
new_dept = {
    "nom": "Marketing",
    "description": "Département Marketing et Communication",
    "chef_departement": 1  # ID d'un employé
}
response = requests.post(f"{BASE_URL}/departements/", json=new_dept, headers=headers)
print_response("POST", "/departements/", response.status_code, response.json())

if response.status_code in [200, 201]:
    dept_id = response.json().get('id')
    print(f"✓ Département créé avec ID: {dept_id}")
    
    # Step 4: Récupérer les détails
    print_header("STEP 4: Détail du Département (GET)")
    response = requests.get(f"{BASE_URL}/departements/{dept_id}/", headers=headers)
    print_response("GET", f"/departements/{dept_id}/", response.status_code, response.json())
    
    # Step 5: Modifier le département
    print_header("STEP 5: Modifier le Département (PATCH)")
    update_data = {
        "nom": "Marketing et Communication",
        "description": "Département Marketing, Communication et Digital"
    }
    response = requests.patch(f"{BASE_URL}/departements/{dept_id}/", json=update_data, headers=headers)
    print_response("PATCH", f"/departements/{dept_id}/", response.status_code, response.json())
    
    # Step 6: Lister à nouveau pour voir les changements
    print_header("STEP 6: Liste mise à jour (GET)")
    response = requests.get(f"{BASE_URL}/departements/", headers=headers)
    print_response("GET", "/departements/", response.status_code, response.json())
    
    # Step 7: Supprimer le département
    print_header("STEP 7: Supprimer le Département (DELETE)")
    response = requests.delete(f"{BASE_URL}/departements/{dept_id}/", headers=headers)
    print(f"\n📌 DELETE /departements/{dept_id}/")
    print(f"Status: {response.status_code}")
    if response.status_code == 204:
        print("✓ Département supprimé avec succès")
    else:
        print(f"Response: {response.json()}")
    
    # Step 8: Vérifier que c'est supprimé
    print_header("STEP 8: Vérification suppression (GET)")
    response = requests.get(f"{BASE_URL}/departements/{dept_id}/", headers=headers)
    print_response("GET", f"/departements/{dept_id}/", response.status_code, response.json())

print_header("✅ TESTS TERMINÉS")
