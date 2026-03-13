from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch

User = get_user_model()

class ManageIATests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User',
        )
        self.client.force_authenticate(user=self.user)

    @patch('manage_ia.services.call_deepseek_api')
    def test_chatbot_ask_success(self, mock_call_api):
        # Mocking la réponse de DeepSeek
        mock_call_api.return_value = "Voici la procédure pour demander un congé."

        url = reverse('chatbot_ask')
        data = {'question': 'Comment demander un congé ?'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn("Voici la procédure", response.data['message'])

    @patch('manage_ia.services.call_deepseek_api')
    def test_chatbot_ask_escalate(self, mock_call_api):
        # Mocker l'escalade
        mock_call_api.return_value = "__ESCALADE_HUMAIN__"

        url = reverse('chatbot_ask')
        data = {'question': 'Quelle est la recette de la fondue ?'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'escalated')
        self.assertIn("transfère vers un agent RH", response.data['message'])

    @patch('manage_ia.services.call_deepseek_api')
    def test_recommend_formations(self, mock_call_api):
        mock_call_api.return_value = "- Formation en gestion\n- Excel avancé"

        url = reverse('recommend_formations')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn("- Formation en gestion", response.data['recommendations'])

    @patch('manage_ia.services.call_deepseek_api')
    def test_admin_trends_unauthorized(self, mock_call_api):
        # Actuellement testuser n'est pas staff ni d'un rôle "admin" ou "manager"
        url = reverse('admin_trends')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('manage_ia.services.call_deepseek_api')
    def test_admin_trends_authorized(self, mock_call_api):
        # Setup admin
        self.user.is_staff = True
        self.user.save()
        
        mock_call_api.return_value = "Les tendances de performance montrent une amélioration."
        
        url = reverse('admin_trends')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn("tendances de performance", response.data['analysis'])
