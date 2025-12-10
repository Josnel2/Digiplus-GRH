# Tests API Badgeage - Guide complet

## 1. Authentification

### Obtenir le token

```bash
curl -X POST http://localhost:8000/api/users/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "employe@example.com",
    "password": "votre_mot_de_passe"
  }'
```

**Réponse:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Sauvegarder le token:**
```bash
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."
```

---

## 2. Gestion des QR Codes

### a) Générer un QR Code pour un employé

```bash
curl -X POST http://localhost:8000/api/users/code-qr/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "employe": 1
  }'
```

**Réponse:**
```json
{
  "id": 1,
  "employe": 1,
  "code_unique": "550e8400-e29b-41d4-a716-446655440000",
  "qr_code_image": "data:image/png;base64,iVBORw0KGgoAAAA...",
  "date_generation": "2025-11-30T10:00:00Z",
  "date_expiration": "2026-11-30T10:00:00Z",
  "actif": true
}
```

### b) Récupérer tous les QR Codes

```bash
curl -X GET http://localhost:8000/api/users/code-qr/ \
  -H "Authorization: Bearer $TOKEN"
```

### c) Récupérer un QR Code spécifique

```bash
curl -X GET http://localhost:8000/api/users/code-qr/1/ \
  -H "Authorization: Bearer $TOKEN"
```

### d) Générer un QR Code (action custom)

```bash
curl -X POST http://localhost:8000/api/users/code-qr/1/generate/ \
  -H "Authorization: Bearer $TOKEN"
```

---

## 3. Enregistrement des Badgeages

### a) Scanner un QR Code (enregistrer badgeage)

```bash
curl -X POST http://localhost:8000/api/users/badgeages/scanner/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code_qr": "70dfef09-804f-4299-9",
    "type": "arrivee",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "device_info": "Mozilla/5.0 (iPhone..."
  }'
```

**Réponse (succès):**
```json
{
  "id": 1,
  "employe": 1,
  "type": "arrivee",
  "datetime": "2025-11-30T08:30:00Z",
  "date": "2025-11-30",
  "localisation_latitude": 48.8566,
  "localisation_longitude": 2.3522,
  "adresse_localisation": "Paris, France",
  "device_info": "Mozilla/5.0 (iPhone..."
}
```

### b) Types de badgeages

| Type | Description | Moment |
|------|-------------|--------|
| `arrivee` | Arrivée à l'office | Matin |
| `depart` | Départ de l'office | Soir |
| `pause_debut` | Début de pause | Midi |
| `pause_fin` | Fin de pause | Après midi |

### c) Récupérer les badgeages du jour

```bash
curl -X GET http://localhost:8000/api/users/badgeages/jour-actuel/ \
  -H "Authorization: Bearer $TOKEN"
```

**Réponse:**
```json
{
  "date": "2025-11-30",
  "employe": 1,
  "badgeages": [
    {
      "id": 1,
      "type": "arrivee",
      "datetime": "2025-11-30T08:30:00Z",
      "localisation_latitude": 48.8566,
      "localisation_longitude": 2.3522
    },
    {
      "id": 2,
      "type": "pause_debut",
      "datetime": "2025-11-30T12:00:00Z",
      "localisation_latitude": 48.8566,
      "localisation_longitude": 2.3522
    },
    {
      "id": 3,
      "type": "pause_fin",
      "datetime": "2025-11-30T13:00:00Z",
      "localisation_latitude": 48.8566,
      "localisation_longitude": 2.3522
    },
    {
      "id": 4,
      "type": "depart",
      "datetime": "2025-11-30T17:30:00Z",
      "localisation_latitude": 48.8566,
      "localisation_longitude": 2.3522
    }
  ]
}
```

### d) Récupérer l'employe actuel (depuis token)

```bash
curl -X GET http://localhost:8000/api/users/badgeages/employe-actuel/ \
  -H "Authorization: Bearer $TOKEN"
```

---

## 4. Gestion des Présences

### a) Récupérer mes présences

```bash
curl -X GET http://localhost:8000/api/users/presences/employe-actuel/ \
  -H "Authorization: Bearer $TOKEN"
```

**Réponse:**
```json
{
  "employe": 1,
  "presences": [
    {
      "id": 1,
      "date": "2025-11-30",
      "statut": "present",
      "heure_arrivee": "08:30:00",
      "heure_depart": "17:30:00",
      "duree_travail_minutes": 540,
      "duree_travail_heures": 9.0,
      "nb_pauses": 1,
      "duree_pauses_minutes": 60,
      "duree_pauses_heures": 1.0
    }
  ]
}
```

### b) Filtrer par mois

```bash
curl -X GET "http://localhost:8000/api/users/presences/mois/?year=2025&month=11" \
  -H "Authorization: Bearer $TOKEN"
```

### c) Récupérer les présences d'un mois spécifique

```bash
curl -X GET "http://localhost:8000/api/users/presences/?date_after=2025-11-01&date_before=2025-11-30" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 5. Rapports de Présence

### a) Récupérer mon rapport mensuel

```bash
curl -X GET http://localhost:8000/api/users/rapports-presence/employe-actuel/ \
  -H "Authorization: Bearer $TOKEN"
```

**Réponse:**
```json
{
  "employe": 1,
  "rapports": [
    {
      "id": 1,
      "employe": 1,
      "annee": 2025,
      "mois": 11,
      "total_jours_present": 20,
      "total_jours_absent": 2,
      "total_jours_retard": 1,
      "total_jours_conge": 1,
      "total_jours_repos": 1,
      "total_heures_travail": "160:30",
      "total_heures_pauses": "20:00",
      "observations": "Aucune observation particulière"
    }
  ]
}
```

### b) Récupérer le rapport pour un employé spécifique (admin)

```bash
curl -X GET "http://localhost:8000/api/users/rapports-presence/?employe=1&annee=2025&mois=11" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 6. Gestion Admin - CRUD

### a) Créer un badgeage (admin)

```bash
curl -X POST http://localhost:8000/api/users/badgeages/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "employe": 1,
    "type": "arrivee",
    "datetime": "2025-11-30T08:30:00Z",
    "localisation_latitude": 48.8566,
    "localisation_longitude": 2.3522
  }'
```

### b) Mettre à jour un badgeage (admin)

```bash
curl -X PATCH http://localhost:8000/api/users/badgeages/1/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "arrivee",
    "localisation_latitude": 48.8567
  }'
```

### c) Supprimer un badgeage (admin)

```bash
curl -X DELETE http://localhost:8000/api/users/badgeages/1/ \
  -H "Authorization: Bearer $TOKEN"
```

### d) Récupérer tous les badgeages (admin)

```bash
curl -X GET http://localhost:8000/api/users/badgeages/ \
  -H "Authorization: Bearer $TOKEN"
```

---

## 7. Scénarios de Test Complets

### Scénario 1: Journée type d'un employé

```bash
# 1. Arrivée à 8:30
curl -X POST http://localhost:8000/api/users/badgeages/scanner/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code_qr": "550e8400-e29b-41d4-a716-446655440000",
    "type": "arrivee",
    "latitude": 48.8566,
    "longitude": 2.3522
  }'

# 2. Pause début à 12:00
curl -X POST http://localhost:8000/api/users/badgeages/scanner/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code_qr": "550e8400-e29b-41d4-a716-446655440000",
    "type": "pause_debut",
    "latitude": 48.8566,
    "longitude": 2.3522
  }'

# 3. Pause fin à 13:00
curl -X POST http://localhost:8000/api/users/badgeages/scanner/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code_qr": "550e8400-e29b-41d4-a716-446655440000",
    "type": "pause_fin",
    "latitude": 48.8566,
    "longitude": 2.3522
  }'

# 4. Départ à 17:30
curl -X POST http://localhost:8000/api/users/badgeages/scanner/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code_qr": "550e8400-e29b-41d4-a716-446655440000",
    "type": "depart",
    "latitude": 48.8566,
    "longitude": 2.3522
  }'

# 5. Vérifier la présence du jour
curl -X GET http://localhost:8000/api/users/presences/employe-actuel/ \
  -H "Authorization: Bearer $TOKEN"

# Résultat attendu:
# - Arrivée: 08:30
# - Départ: 17:30
# - Durée travail: 9h00 - 1h pause = 8h00
# - Statut: present
```

### Scénario 2: Rapport mensuel

```bash
# Vérifier le rapport du mois
curl -X GET http://localhost:8000/api/users/rapports-presence/employe-actuel/ \
  -H "Authorization: Bearer $TOKEN"

# Filtre par mois spécifique
curl -X GET "http://localhost:8000/api/users/presences/mois/?year=2025&month=11" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 8. Erreurs courantes et solutions

### 401 Unauthorized
```
"detail": "Invalid token or token expired"
```
**Solution:** Rafraîchir le token avec le refresh token

### 400 Bad Request
```
"code_qr": ["QR code not found or inactive"]
```
**Solution:** Vérifier que le QR code existe et est actif

### 404 Not Found
```
"detail": "Not found."
```
**Solution:** Vérifier les IDs utilisés

### 403 Forbidden
```
"detail": "You do not have permission to perform this action."
```
**Solution:** Véri que l'utilisateur est admin pour certaines opérations

---

## 9. Pagination et Filtrage

### Récupérer les badgeages avec pagination

```bash
curl -X GET "http://localhost:8000/api/users/badgeages/?page=1&limit=20" \
  -H "Authorization: Bearer $TOKEN"
```

### Filtrer par date

```bash
curl -X GET "http://localhost:8000/api/users/badgeages/?date_after=2025-11-01&date_before=2025-11-30" \
  -H "Authorization: Bearer $TOKEN"
```

### Filtrer par type

```bash
curl -X GET "http://localhost:8000/api/users/badgeages/?type=arrivee" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 10. Import dans Postman

1. Ouvrir Postman
2. Cliquer sur "Import"
3. Coller la collection suivante ou charger `POSTMAN_BADGEAGE_COLLECTION.json`
4. Remplacer `{{TOKEN}}` par le token réel
5. Exécuter les requêtes

**Variables Postman à configurer:**
- `base_url`: `http://localhost:8000/api`
- `token`: (à récupérer après login)
- `employe_id`: 1
- `qr_code`: `550e8400-e29b-41d4-a716-446655440000`
