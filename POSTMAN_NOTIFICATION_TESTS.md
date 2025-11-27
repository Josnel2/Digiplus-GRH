# Guide de Test - Fonctionnalité Notification avec Postman

## 1. Configuration Préalable

### 1.1 Base URL
```
http://localhost:8000
```

### 1.2 Démarrer le serveur Django
```bash
python manage.py runserver
```

### 1.3 Démarrer Daphne (pour WebSocket)
```bash
daphne -b 0.0.0.0 -p 8001 digiplus_hr.asgi:application
```

---

## 2. Scénario de Test - Flux Complet

### **Étape 1 : Authentifier un Admin**

**POST** `/api/login`
```json
{
  "email": "admin@test.com",
  "password": "adminpass123"
}
```

**Réponse attendue** :
```json
{
  "message": "Code OTP envoyé à votre email.",
  "email": "admin@test.com",
  "otp_code": "123456"
}
```

---

### **Étape 2 : Vérifier OTP (Admin)**

**POST** `/api/verify-otp`
```json
{
  "email": "admin@test.com",
  "otp_code": "123456"
}
```

**Réponse attendue** :
```json
{
  "message": "Connexion réussie.",
  "user": {
    "id": 1,
    "email": "admin@test.com",
    "first_name": "Admin",
    "last_name": "User",
    "role": "admin"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

**➜ Copier le token `access` pour les requêtes suivantes**

---

### **Étape 3 : Authentifier un Employé**

**POST** `/api/login`
```json
{
  "email": "employee@test.com",
  "password": "emppass123"
}
```

Puis vérifier l'OTP :

**POST** `/api/verify-otp`
```json
{
  "email": "employee@test.com",
  "otp_code": "654321"
}
```

**➜ Copier le token de l'employé**

---

### **Étape 4 : Créer une Demande de Congé (Employé)**

**POST** `/api/leaves/`

**Headers** :
```
Authorization: Bearer <TOKEN_EMPLOYE>
Content-Type: application/json
```

**Body** :
```json
{
  "type_conge": "annuel",
  "date_debut": "2024-12-01",
  "date_fin": "2024-12-10",
  "description": "Vacances de fin d'année"
}
```

**Réponse attendue** :
```json
{
  "id": 1,
  "employe": 1,
  "type_conge": "annuel",
  "date_debut": "2024-12-01",
  "date_fin": "2024-12-10",
  "description": "Vacances de fin d'année",
  "statut": "en_attente",
  "created_at": "2024-11-26T10:30:00Z",
  "updated_at": "2024-11-26T10:30:00Z"
}
```

**➜ Note l'ID de la demande (ex: 1)**

---

### **Étape 5 : Approuver la Demande (Admin)**

**PATCH** `/api/leaves/1/`

**Headers** :
```
Authorization: Bearer <TOKEN_ADMIN>
Content-Type: application/json
```

**Body** :
```json
{
  "statut": "approuve"
}
```

**Réponse attendue** :
```json
{
  "id": 1,
  "employe": 1,
  "type_conge": "annuel",
  "date_debut": "2024-12-01",
  "date_fin": "2024-12-10",
  "description": "Vacances de fin d'année",
  "statut": "approuve",
  "created_at": "2024-11-26T10:30:00Z",
  "updated_at": "2024-11-26T10:35:00Z"
}
```

**✅ À ce moment :**
- Une `Notification` est créée en DB avec le titre "Congé approuvé"
- Un message WebSocket est envoyé au groupe `user_{employee_id}`

---

### **Étape 6 : Vérifier les Notifications (Employé)**

**GET** `/api/notifications/`

**Headers** :
```
Authorization: Bearer <TOKEN_EMPLOYE>
```

**Réponse attendue** :
```json
[
  {
    "id": 1,
    "demande_conge": 1,
    "titre": "Congé approuvé",
    "message": "Votre demande du 2024-12-01 au 2024-12-10 a été approuvée.",
    "date_envoi": "2024-11-26T10:35:00Z",
    "lu": false
  }
]
```

---

### **Étape 7 : Rejeter une Demande (Admin)**

Créer une autre demande de congé d'abord :

**POST** `/api/leaves/` (avec TOKEN_EMPLOYE)
```json
{
  "type_conge": "maladie",
  "date_debut": "2024-12-15",
  "date_fin": "2024-12-20"
}
```

Puis rejeter :

**PATCH** `/api/leaves/2/`

**Headers** :
```
Authorization: Bearer <TOKEN_ADMIN>
```

**Body** :
```json
{
  "statut": "rejete"
}
```

**Réponse attendue** :
```json
{
  "id": 2,
  "employe": 1,
  "type_conge": "maladie",
  "date_debut": "2024-12-15",
  "date_fin": "2024-12-20",
  "statut": "rejete",
  "created_at": "2024-11-26T10:40:00Z",
  "updated_at": "2024-11-26T10:42:00Z"
}
```

**✅ À ce moment :**
- Une nouvelle `Notification` est créée avec le titre "Congé rejeté"

---

### **Étape 8 : Vérifier à nouveau les Notifications**

**GET** `/api/notifications/`

**Headers** :
```
Authorization: Bearer <TOKEN_EMPLOYE>
```

**Réponse attendue** :
```json
[
  {
    "id": 2,
    "demande_conge": 2,
    "titre": "Congé rejeté",
    "message": "Votre demande du 2024-12-15 au 2024-12-20 a été rejetée.",
    "date_envoi": "2024-11-26T10:42:00Z",
    "lu": false
  },
  {
    "id": 1,
    "demande_conge": 1,
    "titre": "Congé approuvé",
    "message": "Votre demande du 2024-12-01 au 2024-12-10 a été approuvée.",
    "date_envoi": "2024-11-26T10:35:00Z",
    "lu": false
  }
]
```

---

## 3. Test WebSocket (Notifications en Temps Réel)

### 3.1 Dans Postman (WebSocket)

1. **Créer une nouvelle requête WebSocket**
   - URL: `ws://localhost:8001/ws/notifications/`

2. **Ajouter le token JWT en header** :
   ```
   Authorization: Bearer <TOKEN_EMPLOYE>
   ```

3. **Se connecter**
   - Attendre le message de connexion

4. **Approuver une demande** (dans une autre fenêtre Postman en HTTP)
   - **PATCH** `/api/leaves/1/` avec `{"statut": "approuve"}`

5. **Vérifier le WebSocket** :
   - Vous devriez recevoir :
   ```json
   {
     "titre": "Congé approuvé",
     "message": "Votre demande du 2024-12-01 au 2024-12-10 a été approuvée.",
     "demande_id": 1,
     "statut": "approuve"
   }
   ```

---

## 4. Cas de Test Supplémentaires

### 4.1 Approuver avec champs additionnels

**PATCH** `/api/leaves/1/`

```json
{
  "statut": "approuve",
  "description": "Approuvé - Congé confirmé pour les dates prévues"
}
```

**Vérification** :
- La description est mise à jour
- Une seule `Notification` est créée (pas de duplication)

---

### 4.2 Refuser une demande avec raison

**PATCH** `/api/leaves/2/`

```json
{
  "statut": "rejete",
  "description": "Rejeté - Période non disponible suite à réunion importante"
}
```

---

### 4.3 Lister les demandes de congé

**GET** `/api/leaves/`

**Headers** :
```
Authorization: Bearer <TOKEN_EMPLOYE>
```

**Réponse** : Liste uniquement les demandes de l'employé connecté

---

## 5. Points de Vérification

### ✅ Checklist Fonctionnelle

- [ ] Création demande congé crée notification WebSocket pour admins
- [ ] Approbation demande crée `Notification` en DB
- [ ] Approbation demande envoie WebSocket à l'employé
- [ ] Rejet demande crée `Notification` en DB
- [ ] Rejet demande envoie WebSocket à l'employé
- [ ] Champs additionnels sont mis à jour sans duplication notification
- [ ] `/api/notifications/` retourne uniquement les notifications de l'utilisateur
- [ ] Pas de duplication notification lors d'approbation/rejet
- [ ] WebSocket reçoit le payload complet avec titre, message, demande_id, statut

---

## 6. Dépannage

### Problème : Pas de WebSocket reçu

**Solution** :
1. Vérifier que Daphne tourne sur le port 8001
2. Vérifier le token JWT dans les headers
3. Vérifier que l'utilisateur est authentifié (`is_verified=True`)

### Problème : Erreur 401 sur `/api/leaves/`

**Solution** :
1. Vérifier que le token est valide
2. Vérifier le header `Authorization: Bearer <TOKEN>`
3. Vérifier que l'utilisateur est vérifié

### Problème : Notification créée deux fois

**Solution** :
- Vérifier que `perform_update` n'appelle pas `serializer.save()` après `approuver()` / `rejeter()`
- Les méthodes modèle gèrent la persistance

---

## 7. Résumé des Endpoints

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/login` | Connexion + envoi OTP |
| POST | `/api/verify-otp` | Vérifier OTP + recevoir tokens |
| POST | `/api/leaves/` | Créer demande congé |
| GET | `/api/leaves/` | Lister demandes congé |
| PATCH | `/api/leaves/{id}/` | Approuver/Rejeter demande |
| GET | `/api/notifications/` | Lister notifications |
| WS | `/ws/notifications/` | WebSocket notifications temps réel |

---

## 8. Exportation Postman

Vous pouvez importer cette collection Postman :

**Variables** :
```
base_url: http://localhost:8000
ws_url: ws://localhost:8001
admin_token: <TOKEN_ADMIN>
employee_token: <TOKEN_EMPLOYE>
leave_id: <LEAVE_ID>
```

Créer les requêtes avec ces variables pour une réutilisabilité maximale.
