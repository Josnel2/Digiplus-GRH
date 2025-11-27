import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from manage_users.models import Poste, Employe
from manage_users.serializers import (
    PosteSerializer,
    UserSerializer,
    EmployeSerializer,
    CreateEmployeSerializer,
    UpdateEmployeSerializer
)

User = get_user_model()

class TestPosteSerializer:
    """Tests for PosteSerializer"""
    
    def test_poste_serializer_valid_data(self):
        """Test PosteSerializer with valid data"""
        data = {
            'titre': 'Développeur Mobile',
            'description': 'Développement applications mobiles',
            'salaire_de_base': 3800.00
        }
        
        serializer = PosteSerializer(data=data)
        assert serializer.is_valid()
        
        poste = serializer.save()
        assert poste.titre == 'Développeur Mobile'
        assert poste.salaire_de_base == 3800.00
    
    def test_poste_serializer_missing_required_fields(self):
        """Test PosteSerializer with missing required fields"""
        data = {
            'description': 'Description seulement'
        }
        
        serializer = PosteSerializer(data=data)
        assert not serializer.is_valid()
        assert 'titre' in serializer.errors
        assert 'salaire_de_base' in serializer.errors

class TestUserSerializer:
    """Tests for UserSerializer"""
    
    def test_user_serializer(self, admin_user):
        """Test UserSerializer serialization"""
        serializer = UserSerializer(admin_user)
        
        data = serializer.data
        assert data['email'] == 'admin@digiplus.com'
        assert data['first_name'] == 'Admin'
        assert data['last_name'] == 'User'
        assert data['role'] == 'admin'
        assert 'id' in data
        assert 'created_at' in data

class TestEmployeSerializer:
    """Tests for EmployeSerializer"""
    
    def test_employe_serializer(self, employe):
        """Test EmployeSerializer serialization"""
        serializer = EmployeSerializer(employe)
        
        data = serializer.data
        assert data['matricule'] == 'EMP001'
        assert data['statut'] == 'actif'
        assert 'user' in data
        assert 'poste_details' in data
        
        user_data = data['user']
        assert user_data['email'] == 'employee@digiplus.com'
        assert user_data['first_name'] == 'Employee'
        assert user_data['last_name'] == 'User'

class TestCreateEmployeSerializer:
    """Tests for CreateEmployeSerializer"""
    
    def test_create_employe_serializer_valid_data(self, poste):
        """Test CreateEmployeSerializer with valid data"""
        data = {
            'email': 'new.employe@digiplus.com',
            'password': 'password123',
            'first_name': 'New',
            'last_name': 'Employe',
            'role': 'employee',
            'matricule': 'NEW001',
            'date_embauche': '2024-03-01',
            'statut': 'actif',
            'adresse': 'Test Address',
            'poste_id': poste.id,
            'telephone': '+33123456789'
        }
        
        serializer = CreateEmployeSerializer(data=data)
        assert serializer.is_valid()
        
        employe = serializer.save()
        assert employe.matricule == 'NEW001'
        assert employe.user.email == 'new.employe@digiplus.com'
        assert employe.user.first_name == 'New'
        assert employe.poste == poste
    
    def test_create_employe_serializer_invalid_email(self):
        """Test CreateEmployeSerializer with invalid email"""
        data = {
            'email': 'invalid-email',
            'password': 'password123',
            'first_name': 'Test',
            'last_name': 'User',
            'matricule': 'TEST001',
            'date_embauche': '2024-01-01'
        }
        
        serializer = CreateEmployeSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors
    
    def test_create_employe_serializer_missing_required_fields(self):
        """Test CreateEmployeSerializer with missing required fields"""
        data = {
            'email': 'test@digiplus.com',
            # Missing password, first_name, last_name, matricule, date_embauche
        }
        
        serializer = CreateEmployeSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors
        assert 'first_name' in serializer.errors
        assert 'last_name' in serializer.errors
        assert 'matricule' in serializer.errors
        assert 'date_embauche' in serializer.errors

class TestUpdateEmployeSerializer:
    """Tests for UpdateEmployeSerializer"""
    
    def test_update_employe_serializer(self, employe):
        """Test UpdateEmployeSerializer"""
        data = {
            'adresse': 'Nouvelle adresse',
            'telephone': '+33987654321',
            'email': 'updated@digiplus.com',
            'first_name': 'Updated'
        }
        
        serializer = UpdateEmployeSerializer(employe, data=data, partial=True)
        assert serializer.is_valid()
        
        updated_employe = serializer.save()
        assert updated_employe.adresse == 'Nouvelle adresse'
        assert updated_employe.telephone == '+33987654321'
        assert updated_employe.user.email == 'updated@digiplus.com'
        assert updated_employe.user.first_name == 'Updated'
    
    def test_update_employe_serializer_invalid_role(self, employe):
        """Test UpdateEmployeSerializer with invalid role"""
        data = {
            'role': 'invalid_role'
        }
        
        serializer = UpdateEmployeSerializer(employe, data=data, partial=True)
        # This should be valid at serializer level, validation happens at model level
        assert serializer.is_valid()