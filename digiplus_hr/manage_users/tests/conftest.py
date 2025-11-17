import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from manage_users.models import Poste, Employe

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user():
    return User.objects.create_user(
        email='admin@digiplus.com',
        password='adminpass123',
        first_name='Admin',
        last_name='User',
        role='admin'
    )

@pytest.fixture
def hr_user():
    return User.objects.create_user(
        email='hr@digiplus.com',
        password='hrpass123',
        first_name='HR',
        last_name='User',
        role='hr'
    )

@pytest.fixture
def manager_user():
    return User.objects.create_user(
        email='manager@digiplus.com',
        password='managerpass123',
        first_name='Manager',
        last_name='User',
        role='manager'
    )

@pytest.fixture
def employee_user():
    return User.objects.create_user(
        email='employee@digiplus.com',
        password='employeepass123',
        first_name='Employee',
        last_name='User',
        role='employee'
    )

@pytest.fixture
def poste():
    return Poste.objects.create(
        titre='Développeur Fullstack',
        description='Développement applications web',
        salaire_de_base=3500.00
    )

@pytest.fixture
def employe(employee_user, poste):
    return Employe.objects.create(
        user=employee_user,
        matricule='EMP001',
        date_embauche='2024-01-15',
        statut='actif',
        adresse='123 Rue de Paris',
        poste=poste,
        telephone='+33123456789'
    )

@pytest.fixture
def employe_data(poste):
    return {
        'email': 'new.employee@digiplus.com',
        'password': 'newpass123',
        'first_name': 'New',
        'last_name': 'Employee',
        'role': 'employee',
        'matricule': 'EMP002',
        'date_embauche': '2024-02-01',
        'statut': 'actif',
        'adresse': '456 Avenue des Champs',
        'poste_id': poste.id,
        'telephone': '+33987654321',
        'date_naissance': '1990-05-20'
    }