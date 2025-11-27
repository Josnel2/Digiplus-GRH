from django.test import TestCase
from rest_framework.test import APIRequestFactory
from manage_users.permissions import IsSuperAdmin, IsAdmin, IsAdminOrEmployee

class TestPermissions(TestCase):
    """Tests for custom permissions"""
    
    def test_is_superadmin_permission_authorized(self):
        """Test IsSuperAdmin permission with superadmin user"""
        factory = APIRequestFactory()
        request = factory.get('/')
        
        # Create a superadmin user
        from manage_users.models import User
        superadmin_user = User.objects.create_user(
            email='superadmin@digiplus.com',
            password='testpass123',
            role='superadmin'
        )
        request.user = superadmin_user
        
        permission = IsSuperAdmin()
        self.assertTrue(permission.has_permission(request, None))
    
    def test_is_superadmin_permission_unauthorized(self):
        """Test IsSuperAdmin permission with non-superadmin user"""
        factory = APIRequestFactory()
        request = factory.get('/')
        
        # Create an admin user (not superadmin)
        from manage_users.models import User
        admin_user = User.objects.create_user(
            email='admin@digiplus.com',
            password='testpass123',
            role='admin'
        )
        request.user = admin_user
        
        permission = IsSuperAdmin()
        self.assertFalse(permission.has_permission(request, None))
    
    def test_is_admin_permission_superadmin(self):
        """Test IsAdmin permission with superadmin user"""
        factory = APIRequestFactory()
        request = factory.get('/')
        
        from manage_users.models import User
        superadmin_user = User.objects.create_user(
            email='superadmin@digiplus.com',
            password='testpass123',
            role='superadmin'
        )
        request.user = superadmin_user
        
        permission = IsAdmin()
        self.assertTrue(permission.has_permission(request, None))
    
    def test_is_admin_permission_admin(self):
        """Test IsAdmin permission with admin user"""
        factory = APIRequestFactory()
        request = factory.get('/')
        
        from manage_users.models import User
        admin_user = User.objects.create_user(
            email='admin@digiplus.com',
            password='testpass123',
            role='admin'
        )
        request.user = admin_user
        
        permission = IsAdmin()
        self.assertTrue(permission.has_permission(request, None))
    
    def test_is_admin_permission_employee_denied(self):
        """Test IsAdmin permission with employee user (should be denied)"""
        factory = APIRequestFactory()
        request = factory.get('/')
        
        from manage_users.models import User
        employee_user = User.objects.create_user(
            email='employee@digiplus.com',
            password='testpass123',
            role='employee'
        )
        request.user = employee_user
        
        permission = IsAdmin()
        self.assertFalse(permission.has_permission(request, None))
    
    def test_is_admin_or_employee_permission_all_roles(self):
        """Test IsAdminOrEmployee permission with all roles"""
        factory = APIRequestFactory()
        
        from manage_users.models import User
        
        # Test superadmin
        superadmin_user = User.objects.create_user(
            email='superadmin@digiplus.com',
            password='testpass123',
            role='superadmin'
        )
        request = factory.get('/')
        request.user = superadmin_user
        permission = IsAdminOrEmployee()
        self.assertTrue(permission.has_permission(request, None))
        
        # Test admin
        admin_user = User.objects.create_user(
            email='admin@digiplus.com',
            password='testpass123',
            role='admin'
        )
        request = factory.get('/')
        request.user = admin_user
        self.assertTrue(permission.has_permission(request, None))
        
        # Test employee
        employee_user = User.objects.create_user(
            email='employee@digiplus.com',
            password='testpass123',
            role='employee'
        )
        request = factory.get('/')
        request.user = employee_user
        self.assertTrue(permission.has_permission(request, None))