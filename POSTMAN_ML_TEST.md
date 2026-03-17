# Guide de Test Postman pour les API ML Prédictives

Ce guide couvre les endpoints ML ajoutés pour la prédiction des absences et retards.

## Pré-requis

Lancer le projet localement :

```powershell
cd c:\Users\GENIUS ELECTRONICS\Digiplus-GRH\digiplus_hr
..\env\Scripts\python.exe manage.py generate_ml_mock_data
..\env\Scripts\python.exe manage.py train_ml_models
..\env\Scripts\python.exe manage.py runserver
```

Le modèle entraîné est sauvegardé dans :

`digiplus_hr/manage_ia/models_bin/absence_model.joblib`

## Authentification

Avant d'appeler les routes ML, récupérez un token JWT valide.

### 1. Login

**Méthode** : `POST`  
**URL** : `http://127.0.0.1:8000/api/users/login/`

**Body JSON** :

```json
{
  "email": "testuser@example.com",
  "password": "testpassword123"
}
```

### 2. Vérification OTP

**Méthode** : `POST`  
**URL** : `http://127.0.0.1:8000/api/users/verify-otp/`

**Body JSON** :

```json
{
  "email": "testuser@example.com",
  "otp_code": "123456"
}
```

Récupérez ensuite `tokens.access` et utilisez-le dans Postman :

```http
Authorization: Bearer <access_token>
```

## Variables Postman recommandées

Créez un environnement Postman avec :

- `base_url = http://127.0.0.1:8000`
- `access_token = votre_token_jwt`

Puis utilisez ce header :

```http
Authorization: Bearer {{access_token}}
```

## 1. Prédiction pour l'utilisateur connecté

**Méthode** : `GET`  
**URL** : `{{base_url}}/api/ia/predict/absences/`

**Headers** :

- `Authorization: Bearer {{access_token}}`

### Réponse attendue

```json
{
  "employe_id": 7,
  "target_date": "2026-03-16",
  "risk_probability": 0.0689,
  "risk_percent": 6.89,
  "risk_level": "low",
  "features": {
    "department": "RH",
    "day_of_week": 0,
    "month": 3,
    "age_days": 12045,
    "tenure_days": 820,
    "tardies_last_30d": 2,
    "absences_last_30d": 1,
    "leaves_last_30d": 0,
    "attendance_rate_last_30d": 0.96,
    "on_approved_leave": 0
  }
}
```

## 2. Prédiction pour un employé précis

Cette route est surtout utile pour un admin ou un manager.

**Méthode** : `GET`  
**URL** : `{{base_url}}/api/ia/predict/absences/?employe_id=7`

**Headers** :

- `Authorization: Bearer {{access_token}}`

### Cas d'erreur possibles

- `403 Forbidden` : utilisateur non autorisé
- `404 Not Found` : employé introuvable
- `400 Bad Request` : historique insuffisant pour calculer la prédiction
- `503 Service Unavailable` : modèle non entraîné

## 3. Résumé prédictif d'un département

Cette route nécessite un compte admin/staff.

**Méthode** : `GET`  
**URL** : `{{base_url}}/api/ia/predict/department-summary/?departement_id=1`

**Headers** :

- `Authorization: Bearer {{access_token}}`

### Réponse attendue

```json
{
  "departement_id": 1,
  "predictions_count": 4,
  "average_risk_percent": 28.31,
  "high_risk_count": 1,
  "predictions": [
    {
      "employe_id": 7,
      "target_date": "2026-03-16",
      "risk_probability": 0.0689,
      "risk_percent": 6.89,
      "risk_level": "low",
      "features": {
        "department": "RH",
        "day_of_week": 0,
        "month": 3,
        "age_days": 12045,
        "tenure_days": 820,
        "tardies_last_30d": 2,
        "absences_last_30d": 1,
        "leaves_last_30d": 0,
        "attendance_rate_last_30d": 0.96,
        "on_approved_leave": 0
      }
    }
  ],
  "skipped": []
}
```

## Erreurs fréquentes

### `503 Service Unavailable`

Le modèle n'a pas encore été entraîné.

Solution :

```powershell
..\env\Scripts\python.exe manage.py train_ml_models
```

### `400 Bad Request`

L'employé n'a pas encore assez d'historique de présence exploitable.

Solution :

```powershell
..\env\Scripts\python.exe manage.py generate_ml_mock_data
```

### `403 Forbidden`

Le token appartient à un utilisateur sans droits admin/staff pour les routes avancées.

## Requêtes Postman à créer

- `Predict Absence - Me`
- `Predict Absence - By Employee`
- `Predict Department Summary`

## Vérification rapide en local

Si besoin, vous pouvez aussi vérifier hors Postman :

```powershell
cd c:\Users\GENIUS ELECTRONICS\Digiplus-GRH\digiplus_hr
..\env\Scripts\python.exe manage.py test manage_ia -v 1
```
