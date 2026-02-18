#!/usr/bin/env python
"""
Script de test des endpoints de badgeage et présence
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
    f"{BASE_URL}/login/",
    json={"email": "chef.it@example.com", "password": "pass123"}
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

USER_ID = 2  # ID du User (employé)

# Step 2: Lister les QR codes
print_header("STEP 2: Liste des QR Codes (GET)")
response = requests.get(f"{BASE_URL}/code-qr/", headers=headers)
print_response("GET", "/code-qr/", response.status_code, response.json())

if response.status_code == 200 and response.json().get('results'):
    code_qr = response.json()['results'][0].get('code_unique')
    print(f"✓ QR Code trouvé: {code_qr}")
else:
    print("⚠️  Pas de QR code trouvé, création...")
    response = requests.post(f"{BASE_URL}/code-qr/me/regenerate/", json={"user_id": USER_ID}, headers=headers)
    if response.status_code in [200, 201]:
        code_qr = response.json().get('code_unique')
        print(f"✓ QR Code créé: {code_qr}")
    else:
        print(f"❌ Erreur: {response.json()}")
        exit(1)

# Step 3: Scanner le QR code (enregistrer un badgeage)
print_header("STEP 3: Scanner QR Code - Arrivée (POST)")
scanner_data = {
    "user_id": USER_ID,
    "type": "arrivee",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "device_info": "iPhone 12"
}
response = requests.post(f"{BASE_URL}/badgeages/scanner/", json=scanner_data, headers=headers)
print_response("POST", "/badgeages/scanner/", response.status_code, response.json())

# Step 4: Badgeage - Début de pause
print_header("STEP 4: Badgeage - Début de Pause")
pause_debut = {
    "user_id": USER_ID,
    "type": "pause_debut",
    "latitude": 48.8566,
    "longitude": 2.3522
}
response = requests.post(f"{BASE_URL}/badgeages/scanner/", json=pause_debut, headers=headers)
print_response("POST", "/badgeages/scanner/", response.status_code, response.json())

# Step 5: Badgeage - Fin de pause
print_header("STEP 5: Badgeage - Fin de Pause")
pause_fin = {
    "user_id": USER_ID,
    "type": "pause_fin",
    "latitude": 48.8566,
    "longitude": 2.3522
}
response = requests.post(f"{BASE_URL}/badgeages/scanner/", json=pause_fin, headers=headers)
print_response("POST", "/badgeages/scanner/", response.status_code, response.json())

# Step 6: Badgeage - Départ
print_header("STEP 6: Badgeage - Départ")
depart = {
    "user_id": USER_ID,
    "type": "depart",
    "latitude": 48.8566,
    "longitude": 2.3522
}
response = requests.post(f"{BASE_URL}/badgeages/scanner/", json=depart, headers=headers)
print_response("POST", "/badgeages/scanner/", response.status_code, response.json())

# Step 7: Lister les badgeages du jour
print_header("STEP 7: Badgeages du Jour (GET)")
response = requests.get(f"{BASE_URL}/badgeages/jour-actuel/", headers=headers)
print_response("GET", "/badgeages/jour-actuel/", response.status_code, response.json())

# Step 8: Lister tous les badgeages
print_header("STEP 8: Liste Complète des Badgeages (GET)")
response = requests.get(f"{BASE_URL}/badgeages/", headers=headers)
data = response.json()
if isinstance(data, dict) and 'results' in data:
    print(f"Status: {response.status_code}")
    print(f"Total badgeages: {data.get('count', 0)}")
    print(f"Premiers badgeages:\n{json.dumps(data['results'][:2], indent=2, ensure_ascii=False)}")
else:
    print_response("GET", "/badgeages/", response.status_code, data)

# Step 9: Lister les présences
print_header("STEP 9: Liste des Présences (GET)")
response = requests.get(f"{BASE_URL}/presences/", headers=headers)
data = response.json()
if isinstance(data, dict) and 'results' in data:
    print(f"Status: {response.status_code}")
    print(f"Total présences: {data.get('count', 0)}")
    if data['results']:
        print(f"Premiers présences:\n{json.dumps(data['results'][:2], indent=2, ensure_ascii=False)}")
    else:
        print("Pas de présences enregistrées")
else:
    print_response("GET", "/presences/", response.status_code, data)

# Step 10: Présences de l'employé actuel
print_header("STEP 10: Présences de l'Employé (GET)")
response = requests.get(f"{BASE_URL}/presences/employe-actuel/", headers=headers)
print_response("GET", "/presences/employe-actuel/", response.status_code, response.json())

# Step 11: Présences du mois courant
print_header("STEP 11: Présences du Mois Courant (GET)")
response = requests.get(f"{BASE_URL}/presences/mois/?annee=2025&mois=11", headers=headers)
print_response("GET", "/presences/mois/?annee=2025&mois=11", response.status_code, response.json())

# Step 12: Lister les rapports de présence
print_header("STEP 12: Liste des Rapports de Présence (GET)")
response = requests.get(f"{BASE_URL}/rapports-presence/", headers=headers)
data = response.json()
if isinstance(data, dict) and 'results' in data:
    print(f"Status: {response.status_code}")
    print(f"Total rapports: {data.get('count', 0)}")
    if data['results']:
        print(f"Premiers rapports:\n{json.dumps(data['results'][:2], indent=2, ensure_ascii=False)}")
    else:
        print("Pas de rapports enregistrés")
else:
    print_response("GET", "/rapports-presence/", response.status_code, data)

print_header("✅ TESTS TERMINÉS")
