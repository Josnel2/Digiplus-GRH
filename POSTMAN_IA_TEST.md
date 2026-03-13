# Guide de Test Postman pour les API IA (DeepSeek)

Avant de tester, assurez-vous d'avoir un Access Token JWT valide d'un utilisateur connecté (ou d'un administrateur pour certaines routes).
Assurez-vous également que la clé `DEEPSEEK_API` est renseignée dans votre fichier `.env`.

---

## 1. Chatbot RH (IA1 / IA4)
**Méthode** : `POST`
**URL** : `http://127.0.0.1:8000/api/ia/chatbot/ask/`
**Headers** :
  - `Authorization` : `Bearer <votre_token_jwt>`
  - `Content-Type` : `application/json`

**Body (JSON) - Test de réponse normale (IA1)** :
```json
{
    "question": "Quelles sont les démarches pour un congé maternité ?"
}
```
*Le chatbot devrait renvoyer `"status": "success"` avec une réponse détaillée de DeepSeek.*

**Body (JSON) - Test d'escalade (IA4)** :
```json
{
    "question": "Quelle est la recette de la fondue savoyarde ?"
}
```
*Le chatbot devrait renvoyer `"status": "escalated"` avec le message de transfert vers un agent humain, démontrant que DeepSeek comprend qu'il sort de son domaine.*

---

## 2. Recommandations de Formations (IA3)
**Méthode** : `GET`
**URL** : `http://127.0.0.1:8000/api/ia/recommendations/me/`
**Headers** :
  - `Authorization` : `Bearer <votre_token_jwt>`

*La réponse sera `"status": "success"` avec une liste structurée de recommandations de parcours basées sur le rôle et le département de l'utilisateur qui a fait la requête.*

---

## 3. Analyse des Tendances de Performance (IA2)
**Méthode** : `GET`
**URL** : `http://127.0.0.1:8000/api/ia/admin/trends/`
**Headers** :
  - `Authorization` : `Bearer <votre_token_jwt_admin>` *(Note : l'utilisateur doit avoir is_staff=True ou un rôle admin)*

*La réponse sera `"status": "success"` avec un rapport d'analyse de données (taux d'absence, assiduité, etc.) généré par l'IA en fonction des indicateurs fournis.*

---

## 4. Gestion des Documents RAG (Admin)

Ces routes permettent d'alimenter la base de connaissances du Chatbot.

### 4.1. Lister les documents
**Méthode** : `GET`
**URL** : `http://127.0.0.1:8000/api/ia/documents/`
**Headers** :
  - `Authorization` : `Bearer <votre_token_jwt>`

*Retourne la liste complète des documents (id, titre, date d'upload, statut d'indexation).*

### 4.2. Ajouter un nouveau document PDF
**Méthode** : `POST`
**URL** : `http://127.0.0.1:8000/api/ia/documents/`
**Headers** :
  - `Authorization` : `Bearer <votre_token_jwt_admin>` *(Note : l'utilisateur doit avoir is_staff=True ou un rôle admin)*
**Body (form-data)** :
  - `title` : (Text) "Statut Général de la Fonction Publique"
  - `file` : (File) *Sélectionnez un fichier PDF depuis votre ordinateur*

*Le document sera lu, son texte découpé et vectorisé dans FAISS. `is_indexed` passera à `true`.*

### 4.3. Supprimer un document
**Méthode** : `DELETE`
**URL** : `http://127.0.0.1:8000/api/ia/documents/<id_du_document>/`
**Headers** :
  - `Authorization` : `Bearer <votre_token_jwt_admin>`

*Supprime le document de la base de données et supprime le fichier PDF physiquement.*
