from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from manage_users.models import Departement, Employe, Poste
from manage_ia.services import call_deepseek_api

User = get_user_model()


class ManageIATests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword123",
            first_name="Test",
            last_name="User",
        )
        self.client.force_authenticate(user=self.user)

    @patch("manage_ia.services.call_deepseek_api")
    def test_chatbot_ask_success(self, mock_call_api):
        mock_call_api.return_value = "Voici la procedure pour demander un conge."

        url = reverse("chatbot_ask")
        response = self.client.post(url, {"question": "Comment demander un conge ?"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertIn("procedure", response.data["message"])

    @patch("manage_ia.services.call_deepseek_api")
    def test_chatbot_ask_escalate(self, mock_call_api):
        mock_call_api.return_value = "__ESCALADE_HUMAIN__"

        url = reverse("chatbot_ask")
        response = self.client.post(url, {"question": "Quelle est la recette de la fondue ?"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "escalated")

    @patch("manage_ia.services.call_deepseek_api")
    def test_recommend_formations(self, mock_call_api):
        mock_call_api.return_value = "- Formation en gestion\n- Excel avance"

        url = reverse("recommend_formations")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")

    @patch("manage_ia.services.call_deepseek_api")
    def test_admin_trends_unauthorized(self, mock_call_api):
        url = reverse("admin_trends")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("manage_ia.services.call_deepseek_api")
    def test_admin_trends_authorized(self, mock_call_api):
        self.user.is_staff = True
        self.user.save()
        mock_call_api.return_value = "Les tendances de performance montrent une amelioration."

        url = reverse("admin_trends")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")

    @patch("manage_ia.views.absence_inference_service.predict_for_employee")
    def test_predict_absence_me(self, mock_predict):
        departement = Departement.objects.create(nom="RH")
        poste = Poste.objects.create(titre="Analyste", departement=departement, salaire_de_base=50000)
        Employe.objects.create(user=self.user, matricule="EMP001", poste=poste)

        mock_predict.return_value = {
            "employe_id": 1,
            "target_date": "2026-03-16",
            "risk_probability": 0.66,
            "risk_percent": 66.0,
            "risk_level": "medium",
            "features": {},
        }

        url = reverse("predict_absence")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["risk_level"], "medium")

    def test_predict_department_summary_unauthorized(self):
        url = reverse("predict_department_summary")
        response = self.client.get(url, {"departement_id": 1})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("manage_ia.views.absence_inference_service.predict_for_department")
    def test_predict_department_summary_authorized(self, mock_predict):
        self.user.is_staff = True
        self.user.save()
        mock_predict.return_value = {
            "departement_id": 1,
            "predictions_count": 2,
            "average_risk_percent": 52.5,
            "high_risk_count": 1,
            "predictions": [],
            "skipped": [],
        }

        url = reverse("predict_department_summary")
        response = self.client.get(url, {"departement_id": 1})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["departement_id"], 1)

    @override_settings(DEEPSEEK_API_URL="test-api-key", DEEPSEEK_DEFAULT_MODEL="deepseek-chat")
    @patch("manage_ia.services.requests.post")
    def test_call_deepseek_api_uses_default_chat_model(self, mock_post):
        mock_post.return_value.json.return_value = {
            "choices": [{"message": {"content": "ok"}}]
        }
        mock_post.return_value.raise_for_status.return_value = None

        result = call_deepseek_api([{"role": "user", "content": "Bonjour"}])

        self.assertEqual(result, "ok")
        self.assertEqual(mock_post.call_args.kwargs["json"]["model"], "deepseek-chat")
