# Intégration Frontend — Système de Badgeage (QR Code)

Ce document décrit **uniquement** comment intégrer le système de badgeage côté frontend (web ou mobile) avec l’API Django.

## 1) Pré-requis

- Base URL local: `http://127.0.0.1:8000`
- API prefix: `http://127.0.0.1:8000/api/users/`
- Auth: JWT obligatoire sur toutes les routes de badgeage

Header commun:

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

## 2) Authentification (flow OTP -> JWT)

### 2.1 Login (envoi OTP)

- **Endpoint**: `POST /api/users/login/`
- **Body**:

```json
{
  "email": "user@example.com",
  "password": "password"
}
```

- **Résultat**: un OTP est envoyé par email.

### 2.2 Vérifier OTP (obtenir tokens)

- **Endpoint**: `POST /api/users/verify-otp/`
- **Body**:

```json
{
  "email": "user@example.com",
  "otp_code": "123456"
}
```

- **Résultat**: retour `access` + `refresh`.

### 2.3 Récupérer l’identité courante

- **Endpoint**: `GET /api/users/profile/`

Tu en as besoin pour:

- connaître le `user_id` de l’utilisateur connecté
- afficher un écran “Mon QR” / “Pointer”

## 3) QR Code côté Frontend

Objectif UI:

- Un écran **Mon QR code** (affichage)
- Un bouton **Télécharger** (ou partager)
- Un bouton **Régénérer** (si QR compromis)

### 3.1 Récupérer/Créer le QR actif

- **Endpoint**: `GET /api/users/code-qr/me/?user_id=<id>`
- **Auth**: Bearer token

Cas d’usage:

- Employé: `user_id` = id de l’utilisateur connecté
- Admin: peut demander le QR d’un autre utilisateur (selon permissions)

### 3.2 Afficher le QR (image)

- **Endpoint**: `GET /api/users/code-qr/me/download/?user_id=<id>`
- **Retour**: un fichier PNG

Intégration recommandée:

- Web (React/Vue/etc.):
  - faire un `fetch` en `blob`
  - convertir en URL via `URL.createObjectURL(blob)`
  - afficher dans `<img src="..." />`

### 3.3 Régénérer le QR

- **Endpoint**: `POST /api/users/code-qr/me/regenerate/`
- **Body**:

```json
{
  "user_id": 2
}
```

- **Effet**:
  - désactive l’ancien QR actif (`actif=false`)
  - crée un nouveau QR actif
  - génère le PNG du QR

## 4) Pointer (Badgeage)

## 4.1 Endpoint unique

- **Endpoint**: `POST /api/users/badgeages/scanner/`

### Payload minimal (2 modes)

Tu peux pointer avec:

- **Mode QR (recommandé)**: envoyer `code_unique` (valeur scannée depuis le QR)
- **Mode fallback (compatibilité)**: envoyer `user_id`

#### Mode QR (scan réel)

```json
{
  "code_unique": "a1b2c3d4e5f6",
  "type": "arrivee"
}
```

#### Mode fallback (sans scan)

```json
{
  "user_id": 2,
  "type": "arrivee"
}
```

### Types supportés

- `arrivee`
- `depart`
- `pause_debut`
- `pause_fin`

### Champs optionnels (recommandés)

```json
{
  "user_id": 2,
  "type": "arrivee",
  "device_info": "Mozilla/5.0 ...",
  "latitude": 3.8480,
  "longitude": 11.5021
}
```

## 4.2 Règles métier à connaître (pour l’UX)

Même si le backend valide, le frontend doit anticiper:

- **Arrivée**: 1 seule par jour
- **Départ**: 1 seul par jour
- **Pause**:
  - pas de `pause_debut` avant `arrivee`
  - pas de `pause_fin` si aucune pause en cours

Recommandation UI:

- afficher 4 boutons (Arrivée, Pause début, Pause fin, Départ)
- activer/désactiver selon l’état de la journée
- afficher les erreurs 400 du backend telles quelles (toast/snackbar)

## 5) Consulter l’historique (pour affichage dans l’app)

### 5.1 Badgeages

- **Endpoint**: `GET /api/users/badgeages/`
- Employé: ne voit que ses badgeages
- Admin: voit tout

### 5.2 Présences (résumé)

- **Endpoint**: `GET /api/users/presences/`
- Sert à afficher:
  - statut du jour
  - heures arrivée/départ
  - durée travail
  - pauses

## 6) Combien de QR codes peut-on générer ?

- **Historique**: tu peux générer plusieurs QR codes au fil du temps (ex: en cas de compromission).
- **Actif**: le système est conçu pour qu’un employé ait **un seul QR actif** à un instant.

Pourquoi:

- sécurité (rotation immédiate si fuite)
- simplicité côté frontend (un seul QR valide)

## 7) Deux modes d’intégration (important)

### Mode A — MVP (ce que le backend fait actuellement)

Le pointage utilise **`user_id` + `type`**.

- Avantage: intégration rapide.
- Inconvénient: ce n’est pas un “scan QR” authentique (la caméra n’est pas nécessaire).

### Mode B — Scan QR réel (caméra)

Si tu veux que la caméra scanne un QR et que le backend “reconnaisse” l’employé via le contenu du QR, il faut un endpoint qui accepte **`code_unique`** (ou équivalent).

Actuellement, l'endpoint supporte **les deux**:

- si `code_unique` est fourni: résolution via `CodeQR` actif
- sinon: fallback via `user_id`

## 8) Exemple minimal (pseudo-code)

### 8.1 Pointer arrivée

1. `GET /api/users/profile/` -> récupérer `id`
2. `POST /api/users/badgeages/scanner/` avec `user_id` et `type="arrivee"`
3. `GET /api/users/presences/` -> afficher le résumé

## 9) Checklist Frontend

- gérer tokens (`access`/`refresh`)
- inclure `Authorization: Bearer ...`
- écran “Mon QR” + download + regenerate
- écran “Pointer” avec les 4 actions
- écran “Présences” (résumé)
- écran “Historique badgeages”
