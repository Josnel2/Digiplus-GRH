#!/usr/bin/env python
"""
Script de test simplifié des endpoints de badgeage
"""
import subprocess
import time
import requests
import json
import sys

# Démarrer le serveur en arrière-plan
print("🚀 Démarrage du serveur Django...")
server_proc = subprocess.Popen(
    [sys.executable, "manage.py", "runserver"],
    cwd=r"c:\Users\GENIUS ELECTRONICS\Digiplus-GRH\digiplus_hr",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Attendre que le serveur démarre
print("⏳ Attente du démarrage du serveur (5 secondes)...")
time.sleep(5)

BASE_URL = "http://127.0.0.1:8000/api/users"

def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def print_response(method, endpoint, status, data):
    print(f"\n📌 {method} {endpoint}")
    print(f"Status: {status}")
    if isinstance(data, dict):
        print(f"Response:\n{json.dumps(data, indent=2, ensure_ascii=False)}")
    else:
        print(f"Response: {data}")

try:
    # Step 1: Login
    print_header("STEP 1: Authentification")
    try:
        login_response = requests.post(
            f"{BASE_URL}/login",
            json={"email": "chef.it@example.com", "password": "pass123"},
            timeout=10
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login échoué: {login_response.status_code}")
            print_response("POST", "/login", login_response.status_code, login_response.json())
            sys.exit(1)
        
        login_data = login_response.json()
        print(f"✓ Login réussi - OTP requis")
        print(f"Response: {login_data}")
        
        # Step 1.5: Vérifier OTP
        otp_code = login_data.get('otp_code')
        if not otp_code:
            print("❌ Pas de code OTP dans la réponse")
            sys.exit(1)
        
        print(f"✓ OTP reçu: {otp_code}")
        
        verify_response = requests.post(
            f"{BASE_URL}/verify-otp",
            json={"email": "chef.it@example.com", "otp_code": otp_code},
            timeout=10
        )
        
        if verify_response.status_code != 200:
            print(f"❌ OTP verification échouée: {verify_response.status_code}")
            print_response("POST", "/verify-otp", verify_response.status_code, verify_response.json())
            sys.exit(1)
        
        print(f"✓ OTP vérifié")
        tokens_data = verify_response.json().get('tokens', {})
        access_token = tokens_data.get('access')
        if not access_token:
            print(f"❌ Pas de token dans la réponse: {verify_response.json()}")
            sys.exit(1)
        print(f"✓ Token obtenu: {access_token[:50]}...")
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Erreur de connexion: {e}")
        print(f"Le serveur n'écoute pas sur {BASE_URL}")
        sys.exit(1)
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Step 2: Lister les QR codes
    print_header("STEP 2: Liste des QR Codes (GET)")
    response = requests.get(f"{BASE_URL}/code-qr/", headers=headers)
    data = response.json()
    print_response("GET", "/code-qr/", response.status_code, data)
    
    if response.status_code == 200 and data.get('results'):
        code_qr = data['results'][0].get('code_unique')
        print(f"✓ QR Code trouvé: {code_qr}")
    else:
        print("⚠️  Pas de QR code trouvé, création...")
        new_qr = {"employe": 2}
        response = requests.post(f"{BASE_URL}/code-qr/", json=new_qr, headers=headers)
        if response.status_code in [200, 201]:
            code_qr = response.json().get('code_unique')
            print(f"✓ QR Code créé: {code_qr}")
            print_response("POST", "/code-qr/", response.status_code, response.json())
        else:
            print(f"❌ Erreur: {response.status_code}")
            print_response("POST", "/code-qr/", response.status_code, response.json())
            sys.exit(1)
    
    # Step 3: Scanner le QR code (Arrivée)
    print_header("STEP 3: Scanner QR Code - Arrivée (POST)")
    scanner_data = {
        "code_qr": code_qr,
        "type": "arrivee",
        "latitude": 48.8566,
        "longitude": 2.3522,
        "device_info": "iPhone 12"
    }
    response = requests.post(f"{BASE_URL}/badgeages/scanner/", json=scanner_data, headers=headers)
    print_response("POST", "/badgeages/scanner/", response.status_code, response.json())
    
    # Step 4: Badgeages du jour
    print_header("STEP 4: Badgeages du Jour (GET)")
    response = requests.get(f"{BASE_URL}/badgeages/jour-actuel/", headers=headers)
    print_response("GET", "/badgeages/jour-actuel/", response.status_code, response.json())
    
    # Step 5: Lister tous les badgeages
    print_header("STEP 5: Liste Complète des Badgeages (GET)")
    response = requests.get(f"{BASE_URL}/badgeages/", headers=headers)
    data = response.json()
    print(f"Status: {response.status_code}")
    if isinstance(data, dict) and 'results' in data:
        print(f"Total badgeages: {data.get('count', 0)}")
        if data['results']:
            print(f"Premier badgeage:\n{json.dumps(data['results'][0], indent=2, ensure_ascii=False)}")
    
    # Step 6: Présences
    print_header("STEP 6: Liste des Présences (GET)")
    response = requests.get(f"{BASE_URL}/presences/", headers=headers)
    data = response.json()
    print(f"Status: {response.status_code}")
    if isinstance(data, dict) and 'results' in data:
        print(f"Total présences: {data.get('count', 0)}")
        if data['results']:
            print(f"Première présence:\n{json.dumps(data['results'][0], indent=2, ensure_ascii=False)}")
    
    print_header("✅ TESTS TERMINÉS AVEC SUCCÈS")
    
finally:
    # Arrêter le serveur
    print("\n🛑 Arrêt du serveur...")
    server_proc.terminate()
    server_proc.wait(timeout=5)
