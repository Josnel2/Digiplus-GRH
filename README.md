 # MINSANTE-GRH (Digiplus GRH)
 
 Backend Django/DRF pour la gestion RH (utilisateurs, employés, départements/postes, congés) et un système de **badgeage par QR code** avec calcul automatique des **présences** et **rapports**.
 
 ## Prise en main (quickstart)
 
 ### 1) Installer les dépendances
 
 Le projet Django est dans `digiplus_hr/`.
 
 ```bash
 pip install -r digiplus_hr/requirements.txt
 ```
 
 ### 2) Configurer `.env`
 
 Variables utiles (minimum recommandé):
 
 - `SECRET_KEY`
 - `DEBUG=True` (local)
 - `ALLOWED_HOSTS=localhost,127.0.0.1`
 - `REDIS_URL=redis://localhost:6379`
 - `CORS_ALLOW_ALL_ORIGINS=True` (si tu testes depuis un front séparé en local)
 - `PORTAL_URL` (lien front utilisé dans certains emails)
 
 Notes:
 
 - En **local**, si `DATABASE_URL` n'est pas défini, la base **SQLite** est utilisée.
 - En **prod** (Railway), `DATABASE_URL` doit pointer vers PostgreSQL.
 
 ### 3) Migrer et lancer
 
 ```bash
 python digiplus_hr/manage.py makemigrations
 python digiplus_hr/manage.py migrate
 python digiplus_hr/manage.py runserver
 ```
 
 ### 4) Tester rapidement via Postman / curl
 
 - Congés/notifications/audit: `POSTMAN_QUICK_TEST.md`
 - Badgeage/QR: `TESTS_API_BADGEAGE.md` + `POSTMAN_BADGEAGE_COLLECTION.json`
 
 ## Comment se connecter (flow OTP)
 
 1. `POST /api/users/login/` avec `email` + `password` -> envoie un OTP par email.
 2. `POST /api/users/verify-otp/` avec `email` + `otp_code` -> renvoie `access`/`refresh`.
 3. Utiliser le token:
 
 - Header: `Authorization: Bearer <access>`
 
 Important:
 
 - Certaines réponses contiennent `otp_code` pour debug (à retirer/neutraliser en production).
 
 ## Stack
 
 - **Django** + **Django REST Framework**
 - **JWT** (SimpleJWT)
 - **Channels** + **Redis** (WebSocket / notifications temps réel)
 - **PostgreSQL** (prod Railway) / **SQLite** (local)
 - **Whitenoise** (static)
 
 ## Fonctionnalités déjà implémentées
 
 - **Authentification**
   - Login par `email` + `password` avec **OTP par email**
   - Vérification OTP -> émission de tokens JWT
   - Renvoi OTP
   - Refresh token
 - **Mot de passe oublié (OTP)**
   - Request OTP
   - Resend OTP
   - Verify OTP
   - Reset password
 - **Profil utilisateur**
   - Lecture du profil
   - Mise à jour profil
   - Changement de mot de passe
 - **Gestion RH (CRUD via ViewSets)**
   - Superadmins, Admins, Employés
   - Départements, Postes
   - Profils employés
 - **Congés + Notifications + Audit**
   - Création de demandes de congé (employé)
   - Validation/Rejet (admin)
   - Notifications (lecture + mark-as-read)
   - Audit trail des actions admin
 - **Badgeage QR code**
   - Génération / régénération / téléchargement de QR pour un utilisateur
   - Pointage (arrivée, départ, pause début, pause fin)
   - Calcul automatique des données de présence (résumé quotidien)
   - Endpoints de consultation (badgeages du jour, présences, etc.)
 
 ## Base URL
 
 - Local: `http://127.0.0.1:8000/`
 - API: `http://127.0.0.1:8000/api/users/`
 - Admin Django: `http://127.0.0.1:8000/admin/`
 
 ## Endpoints principaux (raccourci)
 
 Les routes sont exposées sous:
 
- `/api/users/` (routes applicatives)
- `/api/management/` (alias vers les mêmes routes — utilisé côté admin)
 
 ### Auth / OTP
 
 - `POST /api/users/login/`
 - `POST /api/users/verify-otp/`
 - `POST /api/users/resend-otp/`
 - `POST /api/users/token/refresh/`
 
 ### Forgot password
 
 - `POST /api/users/forgot-password/request/`
 - `POST /api/users/forgot-password/resend-otp/`
 - `POST /api/users/forgot-password/verify-otp/`
 - `POST /api/users/forgot-password/reset/`
 
 ### Congés / Notifications
 
 - `GET,POST /api/users/leaves/`
 - `GET,PATCH /api/users/leaves/<id>/`
 - `GET /api/users/mes-demandes/`
 - `GET /api/users/notifications/`
 - `PATCH /api/users/notifications/<id>/mark-read/`
 - `GET /api/management/demandes/`
 - `GET /api/management/audit/`
 
 ### Badgeage / QR Code
 
 - `GET,POST /api/users/code-qr/`
 - `GET /api/users/code-qr/me/?user_id=<id>`
 - `POST /api/users/code-qr/me/regenerate/`
 - `GET /api/users/code-qr/me/download/?user_id=<id>`
 - `POST /api/users/badgeages/scanner/` (requiert `user_id` et `type`)
 - `GET /api/users/badgeages/`
 - `GET /api/users/badgeages/jour-actuel/` (si activé dans votre version)
 - `GET /api/users/presences/`
 
 ## Installation (local)
 
 Prérequis:
 
 - Python 3.11+
 - (Optionnel) Redis local si vous testez Channels/WebSocket
 
 ### 1) Dépendances
 
 ### 2) Variables d’environnement
 
 Le projet utilise `python-decouple`.
 
 Crée un fichier `.env` (à la racine du projet ou dans l’environnement d’exécution) avec au minimum:
 
 - `SECRET_KEY`
 - `DEBUG` (ex: `True` en local, `False` en prod)
 - `ALLOWED_HOSTS` (séparés par virgules)
 - `DATABASE_URL` (optionnel en local; requis en prod Railway)
 - `REDIS_URL` (ex: `redis://localhost:6379`)
 - `CORS_ALLOW_ALL_ORIGINS` (ex: `True` en local si besoin)
 - `PORTAL_URL` (URL du front, utilisée dans certains emails)
 
 ### 3) Migrations + lancement
 
 ```bash
 python digiplus_hr/manage.py makemigrations
 python digiplus_hr/manage.py migrate
 python digiplus_hr/manage.py runserver
 ```
 
 Note: en prod, le serveur ASGI est démarré via `daphne`.

 ## Système de badgeage (QR Code) — explication

 ### Objectif

 Permettre à un employé de **pointer** (arrivée/départ/pause) en s'appuyant sur un **QR code** associé à son compte.

 ### Les objets (simplifié)

 - **CodeQR**: code unique + image PNG + statut `actif`.
 - **Badgeage**: un évènement de pointage (type + datetime) pour un employé.
 - **Presence**: résumé de la journée (heure arrivée/départ, pauses, durée, statut).

 ### Comment obtenir un QR code

 2 cas principaux:

 - **Employé**: récupère *son* QR code.
 - **Admin/Superadmin**: peut générer/récupérer le QR code d'un utilisateur.

 Endpoints utiles:

 - `GET /api/users/code-qr/me/?user_id=<id>`
   - Retourne le QR actif de l'utilisateur ciblé (et peut en créer un si nécessaire).
 - `GET /api/users/code-qr/me/download/?user_id=<id>`
   - Télécharge l'image PNG du QR actif.
 - `POST /api/users/code-qr/me/regenerate/` (body: `user_id`)
   - Régénère un nouveau QR (voir section "combien de QR codes").

 ### Comment pointer (scanner)

 Endpoint:

 - `POST /api/users/badgeages/scanner/`

 Le payload (minimum) attend:

 - `user_id`: l'utilisateur pour lequel on pointe
 - `type`: `arrivee` | `depart` | `pause_debut` | `pause_fin`

 Règles côté serveur (anti-erreurs / anti-doublons):

 - Impossible de pointer `arrivee` 2 fois le même jour.
 - Impossible de pointer `depart` si déjà pointé.
 - Impossible de commencer une pause avant l'arrivée.
 - Impossible d'enchaîner des pauses incohérentes (ex: deux `pause_debut` sans `pause_fin`).

 Résultat:

 - Un objet **Badgeage** est créé.
 - Les données de **Presence** (résumé) sont mises à jour/calculées pour la journée.

 ### Combien de QR codes peut-on générer ?

 - **En pratique**: tu peux générer **autant de QR codes que tu veux** (historique en base),
 - **mais un seul QR code est "actif" à un moment donné** pour un employé.

 Pourquoi ?

 - **Sécurité**: si un QR est compromis (photo partagée, téléphone perdu), on le remplace immédiatement.
 - **Rotation**: `regenerate` désactive les anciens (`actif=False`) et en crée un nouveau.
 - **Simplicité**: l'app cliente n'a qu'un QR "valide" à gérer.

 Ce que fait `regenerate`:

 - désactive les QR actifs existants pour l'employé,
 - crée un nouveau `CodeQR` actif,
 - génère l'image PNG correspondante.

 ## Documentation API — Gestion des présences

 Les présences sont exposées via un `ReadOnlyModelViewSet`:

 - un employé ne voit que **ses** présences,
 - un admin/superadmin voit **toutes** les présences,
 - tout est protégé par JWT (`Authorization: Bearer <access>`).

 ### 1) Étapes (workflow)

 1. Authentifie-toi (login + OTP) pour obtenir un token `access`.
 2. Pointe via `POST /api/users/badgeages/scanner/`.
 3. Le backend crée le **badgeage** et met à jour/crée la **presence** du jour.
 4. Consulte les présences via `GET /api/users/presences/`.

 ### 2) Endpoints

 #### Lister les présences

 - **URL**: `GET /api/users/presences/`
 - **Auth**: obligatoire
 - **Accès**:
   - Employé: ses présences uniquement
   - Admin/Superadmin: toutes les présences
 - **Pagination**: pagination DRF si activée globalement (sinon liste complète)

 Exemple `curl`:

 ```bash
 curl -X GET "http://localhost:8000/api/users/presences/" \
   -H "Authorization: Bearer $TOKEN"
 ```

 #### Détail d'une présence

 - **URL**: `GET /api/users/presences/<id>/`
 - **Auth**: obligatoire
 - **Accès**:
   - Employé: uniquement si la présence lui appartient
   - Admin/Superadmin: accès total

 Exemple `curl`:

 ```bash
 curl -X GET "http://localhost:8000/api/users/presences/1/" \
   -H "Authorization: Bearer $TOKEN"
 ```

 ### 3) Données retournées (champs)

 Le serializer utilise `fields = '__all__'` (tous les champs du modèle `Presence`).
 Les champs typiques sont:

 - `id`
 - `employe` (id)
 - `date`
 - `statut` (ex: `present`, `absent`, ...)
 - `heure_arrivee`
 - `heure_depart`
 - `duree_travail_minutes`
 - `nb_pauses`
 - `duree_pauses_minutes`
 - `created_at` / `updated_at` (si présents dans le modèle)

 ### 4) Exemple d'enchaînement complet (pointer puis lire la présence)

 1) Pointer l'arrivée:

 ```bash
 curl -X POST "http://localhost:8000/api/users/badgeages/scanner/" \
   -H "Authorization: Bearer $TOKEN" \
   -H "Content-Type: application/json" \
   -d '{
     "user_id": 2,
     "type": "arrivee",
     "device_info": "Android"
   }'
 ```

 2) Lister les présences:

 ```bash
 curl -X GET "http://localhost:8000/api/users/presences/" \
   -H "Authorization: Bearer $TOKEN"
 ```
 
 ## Lancer avec Docker
 
 `docker-compose.yml` démarre:
 
 - Service `web` (Django + `daphne`)
 - Service `redis`
 
 ```bash
 docker compose up --build
 ```
 
 L’API sera disponible sur `http://localhost:8000/`.
 
 ## Déploiement Railway
 
 Le projet contient `digiplus_hr/railway.json` (Nixpacks) avec:
 
 - Build: install + `makemigrations` + `collectstatic`
 - Start: `migrate` + `create_superadmin` + `daphne` sur `$PORT`
 
 Variables à configurer côté Railway:
 
 - `DATABASE_URL` (Postgres Railway)
 - `REDIS_URL` (Redis Railway)
 - `SECRET_KEY`
 - `DEBUG=False`
 - `ALLOWED_HOSTS` (inclure votre domaine Railway)
 
 ## Tests / Validation
 
 - **Guide Postman (congés + notifications + audit)**: `POSTMAN_QUICK_TEST.md`
 - **Collection Postman badgeage**: `POSTMAN_BADGEAGE_COLLECTION.json`
 - **Guide complet API badgeage (curl + Postman)**: `TESTS_API_BADGEAGE.md`
 - **Guide fonctionnel badgeage/QR**: `GUIDE_BADGEAGE_QR_CODE.md`
 - **Scripts rapides**:
   - `test_badgeage.py`
   - `test_badgeage_fixed.py`
   - `test_badgeage_simple.py`
   - `test_departements.py`
 - **Tests Django**: `digiplus_hr/manage_users/tests/`

 ### Lancer les tests Django

 ```bash
 python digiplus_hr/manage.py test
 ```

 ### Lancer les scripts de test (exemples)

 ```bash
 python test_badgeage_simple.py
 python test_departements.py
 ```
 
 ## Notes importantes (sécurité)
 
 - **Ne pas exposer** les secrets (ex: `SECRET_KEY`, credentials email, `DATABASE_URL`).
 - Les réponses de certaines routes contiennent `otp_code` "pour debug" (à retirer/neutraliser en production).

 ## Note sur le badgeage `scanner`

 Dans cette version du backend, l'action `POST /api/users/badgeages/scanner/` s'appuie sur un `user_id` + `type` (et applique des règles anti-doublons sur la journée).
