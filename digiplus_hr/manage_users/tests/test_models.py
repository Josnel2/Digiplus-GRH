from django.test import TestCase
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from manage_users.models import User, Poste, Employe

User = get_user_model()

class TestUserModel(TestCase):
    """Tests for User model"""
    
    def setUp(self):
        """Set up test data"""
        self.user_data = {
            'email': 'test@digiplus.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
    
    def test_create_user(self):
        """Test creating a normal user"""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.email, 'test@digiplus.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.role, 'employee')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_create_superuser(self):
        """Test creating a superuser"""
        superuser = User.objects.create_superuser(
            email='superadmin@digiplus.com',
            password='superpass123'
        )
        
        self.assertEqual(superuser.email, 'superadmin@digiplus.com')
        self.assertEqual(superuser.role, 'superadmin')
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
    
    def test_create_admin_user(self):
        """Test creating an admin user"""
        admin_user = User.objects.create_user(
            email='admin@digiplus.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
            role='admin'
        )
        
        self.assertEqual(admin_user.role, 'admin')
        self.assertFalse(admin_user.is_staff)
        self.assertFalse(admin_user.is_superuser)
    
    def test_user_str_representation(self):
        """Test user string representation"""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(str(user), 'Test User (test@digiplus.com)')
    
    def test_unique_email_constraint(self):
        """Test that email must be unique"""
        User.objects.create_user(**self.user_data)
        
        with self.assertRaises(IntegrityError):
            User.objects.create_user(**self.user_data)
    
    def test_user_required_fields(self):
        """Test user required fields"""
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='testpass123')

class TestPosteModel:
    """Tests for Poste model"""
    
    def test_create_poste(self):
        """Test creating a poste"""
        poste = Poste.objects.create(
            titre='Chef de Projet',
            description='Gestion de projets',
            salaire_de_base=4500.00
        )
        
        assert poste.titre == 'Chef de Projet'
        assert poste.description == 'Gestion de projets'
        assert poste.salaire_de_base == 4500.00
        assert poste.created_at is not None
    
    def test_poste_str_representation(self):
        """Test poste string representation"""
        poste = Poste.objects.create(
            titre='Développeur',
            salaire_de_base=3500.00
        )
        
        assert str(poste) == 'Développeur'

class TestEmployeModel:
    """Tests for Employe model"""
    
    def test_create_employe(self, employee_user, poste):
        """Test creating an employe"""
        employe = Employe.objects.create(
            user=employee_user,
            matricule='EMP001',
            date_embauche='2024-01-15',
            statut='actif',
            adresse='123 Rue de Paris',
            poste=poste,
            telephone='+33123456789'
        )
        
        assert employe.matricule == 'EMP001'
        assert employe.user == employee_user
        assert employe.poste == poste
        assert employe.statut == 'actif'
        assert employe.adresse == '123 Rue de Paris'
    
    def test_employe_str_representation(self, employe):
        """Test employe string representation"""
        expected_str = f"EMP001 - {employe.user.get_full_name()}"
        assert str(employe) == expected_str
    
    def test_unique_matricule_constraint(self, employee_user, poste):
        """Test that matricule must be unique"""
        Employe.objects.create(
            user=employee_user,
            matricule='UNIQUE001',
            date_embauche='2024-01-15'
        )
        
        # Create another user for the second employe
        another_user = User.objects.create_user(
            email='another@digiplus.com',
            password='testpass123'
        )
        
        with pytest.raises(IntegrityError):
            Employe.objects.create(
                user=another_user,
                matricule='UNIQUE001',
                date_embauche='2024-01-15'
            )
    
    def test_employe_default_values(self, employee_user):
        """Test employe default values"""
        employe = Employe.objects.create(
            user=employee_user,
            matricule='EMP003',
            date_embauche='2024-01-15'
        )
        
        assert employe.statut == 'actif'
        assert employe.adresse is None
        assert employe.poste is None
        assert employe.telephone is None
        assert employe.date_naissance is None
    
    def test_employe_relationships(self, employe, poste):
        """Test employe relationships"""
        assert employe.user.email == 'employee@digiplus.com'
        assert employe.poste == poste
        assert poste.employes.count() == 1
        assert poste.employes.first() == employe