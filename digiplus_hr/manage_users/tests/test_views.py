import pytest
from django.urls import reverse
from rest_framework import status
from manage_users.models import Poste, Employe

class TestPosteViewSet:
    """Tests for PosteViewSet"""
    
    def test_list_postes_authenticated(self, api_client, admin_user, poste):
        """Test listing postes as authenticated user"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('poste-list')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['titre'] == 'Développeur Fullstack'
    
    def test_list_postes_unauthenticated(self, api_client):
        """Test listing postes as unauthenticated user"""
        url = reverse('poste-list')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_poste_admin(self, api_client, admin_user):
        """Test creating poste as admin"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('poste-list')
        data = {
            'titre': 'Chef de Projet',
            'description': 'Gestion de projets',
            'salaire_de_base': 4500.00
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['titre'] == 'Chef de Projet'
        assert Poste.objects.count() == 1
    
    def test_create_poste_hr(self, api_client, hr_user):
        """Test creating poste as HR"""
        api_client.force_authenticate(user=hr_user)
        url = reverse('poste-list')
        data = {
            'titre': 'Analyste',
            'salaire_de_base': 3000.00
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_create_poste_employee_denied(self, api_client, employee_user):
        """Test creating poste as employee (should be denied)"""
        api_client.force_authenticate(user=employee_user)
        url = reverse('poste-list')
        data = {
            'titre': 'Test Poste',
            'salaire_de_base': 1000.00
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

class TestEmployeViewSet:
    """Tests for EmployeViewSet"""
    
    def test_list_employes_admin(self, api_client, admin_user, employe):
        """Test listing employes as admin"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('employe-list')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['matricule'] == 'EMP001'
    
    def test_list_employes_hr(self, api_client, hr_user, employe):
        """Test listing employes as HR"""
        api_client.force_authenticate(user=hr_user)
        url = reverse('employe-list')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_list_employes_employee_denied(self, api_client, employee_user):
        """Test listing employes as employee (should be denied)"""
        api_client.force_authenticate(user=employee_user)
        url = reverse('employe-list')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_employe_admin(self, api_client):
        """Test creating employe as admin"""
        from manage_users.models import User
        admin_user = User.objects.create_user(
            email='admin@digiplus.com',
            password='adminpass123',
            role='admin'
        )
        api_client.force_authenticate(user=admin_user)
    
    def test_retrieve_employe(self, api_client, admin_user, employe):
        """Test retrieving specific employe"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('employe-detail', kwargs={'pk': employe.id})
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['matricule'] == 'EMP001'
        assert response.data['user']['first_name'] == 'Employee'
    
    def test_update_employe(self, api_client, admin_user, employe):
        """Test updating employe"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('employe-detail', kwargs={'pk': employe.id})
        data = {
            'adresse': 'Nouvelle adresse mise à jour',
            'telephone': '+33111111111'
        }
        
        response = api_client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['adresse'] == 'Nouvelle adresse mise à jour'
        assert response.data['telephone'] == '+33111111111'
    
    def test_delete_employe_soft_delete(self, api_client, admin_user, employe):
        """Test soft delete of employe"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('employe-detail', kwargs={'pk': employe.id})
        
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Refresh from database
        employe.refresh_from_db()
        employe.user.refresh_from_db()
        
        # Check soft delete
        assert employe.statut == 'inactif'
        assert employe.user.is_active is False
    
    def test_activate_employe(self, api_client, admin_user, employe):
        """Test activating a deactivated employe"""
        # First deactivate the employe
        employe.user.is_active = False
        employe.user.save()
        employe.statut = 'inactif'
        employe.save()
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('employe-activate', kwargs={'pk': employe.id})
        
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'Employé activé'
        
        # Refresh and check activation
        employe.refresh_from_db()
        employe.user.refresh_from_db()
        
        assert employe.statut == 'actif'
        assert employe.user.is_active is True
    
    def test_me_endpoint(self, api_client, employe):
        """Test the me endpoint for current user profile"""
        api_client.force_authenticate(user=employe.user)
        url = reverse('employe-me')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['matricule'] == 'EMP001'
        assert response.data['user']['email'] == 'employee@digiplus.com'
    
    def test_me_endpoint_no_employe_profile(self, api_client, admin_user):
        """Test me endpoint when user has no employe profile"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('employe-me')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['error'] == 'Profil employé non trouvé'