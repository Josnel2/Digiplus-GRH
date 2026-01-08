# 📱 Système de Badgeage par QR Code - Guide Complet

## 🎯 Vue d'ensemble

Le système de badgeage permet aux employés de pointer (arrivée/départ) en scannant un QR code unique via leur smartphone. Les données collectées incluent:
- Heure exacte du badgeage
- Type d'action (arrivée, départ, pause)
- Géolocalisation (latitude/longitude optionnelle)
- Type de device utilisé

## 📋 Architecture

```
Employé
  └─> CodeQR (QR unique)
       └─> Badgeages multiples
            └─> Presence (résumé quotidien)
                 └─> RapportPresence (résumé mensuel)
```

## 🗄️ Modèles de Données

### 1. **CodeQR**
Génère un QR code unique pour chaque employé
```python
- employe: ForeignKey(Employe)
- code_unique: CharField (auto-généré)
- qr_code_image: ImageField (PNG automatique)
- date_generation: DateTimeField
- date_expiration: DateField (optionnel)
- actif: Boolean
```

### 2. **Badgeage**
Enregistre chaque pointage
```python
- employe: ForeignKey(Employe)
- type: CharField (arrivee|depart|pause_debut|pause_fin)
- datetime: DateTimeField (auto-généré)
- date: DateField (indexé)
- localisation_latitude: FloatField (optionnel)
- localisation_longitude: FloatField (optionnel)
- adresse_localisation: CharField (optionnel)
- device_info: CharField (ex: "iPhone 12")
```

### 3. **Presence**
Résumé quotidien
```python
- employe: ForeignKey(Employe)
- date: DateField (unique par employé)
- statut: CharField (present|absent|retard|conge|repos)
- heure_arrivee: TimeField
- heure_depart: TimeField
- duree_travail_minutes: IntegerField
- nb_pauses: IntegerField
- duree_pauses_minutes: IntegerField
```

### 4. **RapportPresence**
Résumé mensuel
```python
- employe: ForeignKey(Employe)
- annee: IntegerField
- mois: IntegerField (1-12)
- total_jours_travail: IntegerField
- total_jours_present: IntegerField
- total_jours_absent: IntegerField
- total_jours_retard: IntegerField
- total_jours_conge: IntegerField
- total_jours_repos: IntegerField
- total_heures_travail: DecimalField
- total_heures_pauses: DecimalField
```

## 🌐 Endpoints API

### **1. Gestion des QR Codes**

#### Créer un QR Code
```
POST /api/users/code-qr/
Authorization: Bearer {token}

Body:
{
  "employe": 2
}

Response (201):
{
  "id": 1,
  "employe": 2,
  "employe_info": {
    "id": 2,
    "matricule": "EMP102",
    "nom": "Jean Dupont",
    "email": "chef.it@example.com"
  },
  "code_unique": "a1b2c3d4e5f6",
  "qr_code_image": "/media/qr_codes/qr_EMP102.png",
  "date_generation": "2025-11-30T10:00:00Z",
  "date_expiration": null,
  "actif": true
}
```

#### Lister les QR Codes
```
GET /api/users/code-qr/
Authorization: Bearer {token}

Response (200):
{
  "count": 4,
  "next": null,
  "previous": null,
  "results": [...]
}
```

#### Détail d'un QR Code
```
GET /api/users/code-qr/1/
Authorization: Bearer {token}

Response (200): Comme la création
```

---

### **2. Badgeage (Pointage)**

#### Scanner un QR Code
```
POST /api/users/badgeages/scanner/
Authorization: Bearer {token}
Content-Type: application/json

Body:
{
  "code_qr": "a1b2c3d4e5f6",
  "type": "arrivee",
  "latitude": 48.8566,
  "longitude": 2.3522,
  "device_info": "iPhone 12"
}

Response (201):
{
  "status": "success",
  "message": "Badgeage enregistré: arrivee",
  "badgeage": {
    "id": 5,
    "employe": 2,
    "employe_info": {
      "id": 2,
      "matricule": "EMP102",
      "nom": "Jean Dupont"
    },
    "type": "arrivee",
    "datetime": "2025-11-30T09:15:00Z",
    "date": "2025-11-30",
    "localisation_latitude": 48.8566,
    "localisation_longitude": 2.3522,
    "adresse_localisation": null,
    "device_info": "iPhone 12"
  }
}
```

**Types disponibles:**
- `arrivee` - Arrivée au travail
- `depart` - Départ du travail
- `pause_debut` - Début de pause
- `pause_fin` - Fin de pause

#### Badgeages du Jour
```
GET /api/users/badgeages/jour-actuel/
Authorization: Bearer {token}

Response (200):
{
  "date": "2025-11-30",
  "count": 4,
  "badgeages": [
    {
      "id": 1,
      "type": "arrivee",
      "datetime": "2025-11-30T09:00:00Z",
      ...
    },
    {
      "id": 2,
      "type": "pause_debut",
      "datetime": "2025-11-30T12:00:00Z",
      ...
    },
    {
      "id": 3,
      "type": "pause_fin",
      "datetime": "2025-11-30T12:30:00Z",
      ...
    },
    {
      "id": 4,
      "type": "depart",
      "datetime": "2025-11-30T17:30:00Z",
      ...
    }
  ]
}
```

#### Tous les Badgeages
```
GET /api/users/badgeages/
Authorization: Bearer {token}

Response (200):
{
  "count": 120,
  "next": "...page=2",
  "previous": null,
  "results": [...]
}
```

---

### **3. Présences**

#### Présences de l'Employé
```
GET /api/users/presences/employe-actuel/
Authorization: Bearer {token}

Response (200):
{
  "employe": {
    "id": 2,
    "matricule": "EMP102",
    "nom": "Jean Dupont"
  },
  "count": 21,
  "presences": [
    {
      "id": 8,
      "employe": 2,
      "employe_info": {...},
      "date": "2025-11-30",
      "statut": "present",
      "heure_arrivee": "09:15:00",
      "heure_depart": "17:30:00",
      "duree_travail_minutes": 495,
      "duree_travail_heures": 8.25,
      "nb_pauses": 1,
      "duree_pauses_minutes": 30,
      "duree_pauses_heures": 0.5,
      "remarques": null,
      "created_at": "2025-11-30T10:00:00Z",
      "updated_at": "2025-11-30T17:35:00Z"
    }
  ]
}
```

#### Présences d'un Mois
```
GET /api/users/presences/mois/?annee=2025&mois=11
Authorization: Bearer {token}

Response (200):
{
  "annee": 2025,
  "mois": 11,
  "count": 20,
  "presences": [...]
}
```

#### Tous les Présences
```
GET /api/users/presences/
Authorization: Bearer {token}

Response (200): Paginated list
```

---

### **4. Rapports de Présence**

#### Rapports de l'Employé
```
GET /api/users/rapports-presence/employe-actuel/
Authorization: Bearer {token}

Response (200):
{
  "employe": {
    "id": 2,
    "matricule": "EMP102",
    "nom": "Jean Dupont"
  },
  "count": 2,
  "rapports": [
    {
      "id": 2,
      "employe": 2,
      "employe_info": {...},
      "annee": 2025,
      "mois": 11,
      "total_jours_travail": 20,
      "total_jours_present": 19,
      "total_jours_absent": 0,
      "total_jours_retard": 1,
      "total_jours_conge": 0,
      "total_jours_repos": 0,
      "total_heures_travail": "159.50",
      "total_heures_pauses": "10.00",
      "observations": null,
      "generated_at": "2025-11-30T18:00:00Z"
    }
  ]
}
```

#### Tous les Rapports
```
GET /api/users/rapports-presence/
Authorization: Bearer {token}

Response (200): Paginated list
```

---

## 🔐 Permissions

| Endpoint | GET | POST | PATCH | DELETE |
|----------|-----|------|-------|--------|
| code-qr | Auth | Auth | Auth | Auth |
| badgeages | Auth | Auth | Auth | Auth |
| presences | Auth | Auth | Auth | Auth |
| rapports-presence | Auth (ReadOnly) | ❌ | ❌ | ❌ |

**Rules:**
- Employés voient leurs propres données
- Admins voient toutes les données
- Les rapports sont en lecture seule (générés auto)

---

## 📊 Flux d'Utilisation Typique

### Scenario: Journée de Travail Complète

```
09:00 → POST /badgeages/scanner/ avec type="arrivee"
         ↓
         BD créé: Badgeage(type=arrivee, datetime=09:00)

12:00 → POST /badgeages/scanner/ avec type="pause_debut"
         ↓
         BD créé: Badgeage(type=pause_debut, datetime=12:00)

12:30 → POST /badgeages/scanner/ avec type="pause_fin"
         ↓
         BD créé: Badgeage(type=pause_fin, datetime=12:30)

17:30 → POST /badgeages/scanner/ avec type="depart"
         ↓
         BD créé: Badgeage(type=depart, datetime=17:30)
         
         CALCUL AUTO:
         - Durée travail: 495 minutes (8h15)
         - Pauses: 30 minutes
         - Statut: présent
         
         ↓
         Presence enregistré pour le jour
```

---

## 🛠️ Installation & Setup

### 1. Dépendances
```bash
pip install qrcode[pil] pillow
```

### 2. Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Créer des QR codes
```bash
POST /api/users/code-qr/
{
  "employe": 1
}
```

### 4. Télécharger l'image
Le QR code est automatiquement généré et sauvegardé à:
```
/media/qr_codes/qr_EMP001.png
```

---

## 🧪 Tests

### Script Python
```bash
python test_badgeage.py
```

### Postman Collection
Importer `POSTMAN_BADGEAGE_COLLECTION.json` dans Postman

### Curl Commands

**Scanner un QR code:**
```bash
curl -X POST http://localhost:8000/api/users/badgeages/scanner/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "code_qr": "a1b2c3d4e5f6",
    "type": "arrivee",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "device_info": "iPhone 12"
  }'
```

**Voir les badgeages du jour:**
```bash
curl http://localhost:8000/api/users/badgeages/jour-actuel/ \
  -H "Authorization: Bearer <token>"
```

---

## 📈 Cas d'Usage Avancés

### 1. **Détection de Retard**
```
Si heure_arrivee > 09:00:
  statut = "retard"
```

### 2. **Détection d'Absence**
```
Si aucun badgeage pour la journée:
  statut = "absent"
```

### 3. **Calcul des Heures Supplémentaires**
```
Si duree_travail > 8h:
  heures_supp = duree_travail - 8h
```

### 4. **Export Mensuel**
```
GET /api/users/rapports-presence/employe-actuel/
→ Export PDF/Excel des rapports
```

---

## 🔍 Requêtes Filtrées

### Badgeages par Type
```
GET /api/users/badgeages/?type=arrivee
```

### Présences par Statut
```
GET /api/users/presences/?statut=retard
```

### Badgeages d'une Date
```
GET /api/users/badgeages/?date=2025-11-30
```

---

## ⚠️ Erreurs Courantes

| Code | Erreur | Solution |
|------|--------|----------|
| 400 | QR code invalide | Vérifier le `code_unique` |
| 400 | QR code désactivé | Générer un nouveau QR code |
| 404 | Employé non trouvé | L'utilisateur doit être lié à un Employe |
| 401 | Token invalide | Ré-authentifier |

---

## 📝 Notes

- ✅ Les QR codes sont générés automatiquement en PNG
- ✅ Les présences sont calculées automatiquement
- ✅ Les géolocalisations sont optionnelles mais recommandées
- ✅ Les rapports sont générés mensuellement
- ✅ Les données sont indexées pour performance

---

## 🚀 Prochaines Étapes

1. ✅ Implémenter le calcul auto des présences (trigger)
2. ✅ Ajouter l'export PDF/Excel des rapports
3. ✅ Implémenter les alertes de retard
4. ✅ Dashboard temps réel des badgeages
5. ✅ App mobile de scan QR
