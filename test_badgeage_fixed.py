#!/usr/bin/env python
"""
Script de test simplifie des endpoints de badgeage
"""
import subprocess
import time
import requests
import json
import sys

# Demarrer le serveur en arriere-plan
print("[*] Demarrage du serveur Django...")
server_proc = subprocess.Popen(
    [sys.executable, "manage.py", "runserver"],
    cwd=r"c:\Users\GENIUS ELECTRONICS\Digiplus-GRH\digiplus_hr",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Attendre que le serveur demarre
print("[*] Attente du demarrage du serveur (5 secondes)...")
time.sleep(5)

BASE_URL = "http://127.0.0.1:8000/api/users"

def print_header(title):
    print("\n" + "="*70)
    print("  " + title)
    print("="*70)

def print_response(method, endpoint, status, data):
    print("\n[->] {} {}".format(method, endpoint))
    print("Status: {}".format(status))
    if isinstance(data, dict):
        print("Response:\n{}".format(json.dumps(data, indent=2, ensure_ascii=False)))
    else:
        print("Response: {}".format(data))

try:
    # Step 1: Login
    print_header("STEP 1: Authentification")
    try:
        login_response = requests.post(
            "{}/login".format(BASE_URL),
            json={"email": "chef.it@example.com", "password": "pass123"},
            timeout=10
        )
        
        if login_response.status_code != 200:
            print("[X] Login echoue: {}".format(login_response.status_code))
            print_response("POST", "/login", login_response.status_code, login_response.json())
            sys.exit(1)
        
        login_data = login_response.json()
        print("[+] Login reussi - OTP requis")
        print("Response: {}".format(login_data))
        
        # Step 1.5: Verifier OTP
        otp_code = login_data.get('otp_code')
        if not otp_code:
            print("[X] Pas de code OTP dans la reponse")
            sys.exit(1)
        
        print("[+] OTP recu: {}".format(otp_code))
        
        verify_response = requests.post(
            "{}/verify-otp".format(BASE_URL),
            json={"email": "chef.it@example.com", "otp_code": otp_code},
            timeout=10
        )
        
        if verify_response.status_code != 200:
            print("[X] OTP verification echouee: {}".format(verify_response.status_code))
            print_response("POST", "/verify-otp", verify_response.status_code, verify_response.json())
            sys.exit(1)
        
        print("[+] OTP verifie")
        tokens_data = verify_response.json().get('tokens', {})
        access_token = tokens_data.get('access')
        if not access_token:
            print("[X] Pas de token dans la reponse: {}".format(verify_response.json()))
            sys.exit(1)
        print("[+] Token obtenu: {}...".format(access_token[:50]))
        
    except requests.exceptions.ConnectionError as e:
        print("[X] Erreur de connexion: {}".format(e))
        print("[X] Le serveur n'ecoute pas sur {}".format(BASE_URL))
        sys.exit(1)
    
    headers = {
        "Authorization": "Bearer {}".format(access_token),
        "Content-Type": "application/json"
    }
    
    # Step 2: Lister les QR codes
    print_header("STEP 2: Liste des QR Codes (GET)")
    response = requests.get("{}/code-qr/".format(BASE_URL), headers=headers)
    data = response.json()
    print_response("GET", "/code-qr/", response.status_code, data)
    
    code_qr = None
    if response.status_code == 200:
        # Vérifier si c'est une liste ou un dict avec 'results'
        if isinstance(data, list) and len(data) > 0:
            code_qr = data[0].get('code_unique')
            print("[+] QR Code trouve (dans liste): {}".format(code_qr))
        elif isinstance(data, dict) and data.get('results') and len(data['results']) > 0:
            code_qr = data['results'][0].get('code_unique')
            print("[+] QR Code trouve (dans dict): {}".format(code_qr))
    
    if not code_qr:
        print("[!] Pas de QR code trouve, creation...")
        new_qr = {"employe": 2}
        response = requests.post("{}/code-qr/".format(BASE_URL), json=new_qr, headers=headers)
        if response.status_code in [200, 201]:
            code_qr = response.json().get('code_unique')
            print("[+] QR Code cree: {}".format(code_qr))
            print_response("POST", "/code-qr/", response.status_code, response.json())
        else:
            print("[X] Erreur: {}".format(response.status_code))
            print_response("POST", "/code-qr/", response.status_code, response.json())
            sys.exit(1)
    
    # Step 3: Scanner le QR code (Arrivee)
    print_header("STEP 3: Scanner QR Code - Arrivee (POST)")
    scanner_data = {
        "code_qr": code_qr,
        "type": "arrivee",
        "latitude": 48.8566,
        "longitude": 2.3522,
        "device_info": "iPhone 12"
    }
    response = requests.post("{}/badgeages/scanner/".format(BASE_URL), json=scanner_data, headers=headers)
    print_response("POST", "/badgeages/scanner/", response.status_code, response.json())
    
    # Step 4: Badgeages du jour - Vérifier les différentes variantes
    print_header("STEP 4: Badgeages du Jour (GET) - Variantes")
    
    variants = [
        "/badgeages/jour-actuel/",
        "/badgeages/jour_actuel/",
        "/badgeages/jourActuel/",
        "/badgeages/jour-actuels/",
    ]
    
    for variant in variants:
        url = "{}{}".format(BASE_URL, variant)
        response = requests.get(url, headers=headers)
        print("[->] GET {}".format(variant))
        print("Status: {}".format(response.status_code))
        if response.status_code != 404:
            print("Response: {}".format(response.json()))
        else:
            print("Response: 404 Not Found")
    
    # Step 5: Lister tous les badgeages
    print_header("STEP 5: Liste Complete des Badgeages (GET)")
    response = requests.get("{}/badgeages/".format(BASE_URL), headers=headers)
    data = response.json()
    print("Status: {}".format(response.status_code))
    if isinstance(data, dict) and 'results' in data:
        print("Total badgeages: {}".format(data.get('count', 0)))
        if data['results']:
            print("Premier badgeage:\n{}".format(json.dumps(data['results'][0], indent=2, ensure_ascii=False)))
    
    # Step 6: Presences
    print_header("STEP 6: Liste des Presences (GET)")
    response = requests.get("{}/presences/".format(BASE_URL), headers=headers)
    data = response.json()
    print("Status: {}".format(response.status_code))
    if isinstance(data, dict) and 'results' in data:
        print("Total presences: {}".format(data.get('count', 0)))
        if data['results']:
            print("Premiere presence:\n{}".format(json.dumps(data['results'][0], indent=2, ensure_ascii=False)))
    
    print_header("[OK] TESTS TERMINES AVEC SUCCES")
    
except Exception as e:
    print("[!] Exception: {}".format(e))
    import traceback
    traceback.print_exc()
    
finally:
    # Arreter le serveur
    print("\n[*] Arret du serveur...")
    try:
        server_proc.terminate()
        server_proc.wait(timeout=5)
    except:
        pass
