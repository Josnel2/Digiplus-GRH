import pytest
from rest_framework.test import APIRequestFactory
from manage_users.permissions import IsAdmin, IsAdminOrHR, IsAdminOrHROrManager

class TestPermissions:
    """Tests for custom permissions"""
    
    def test_is_admin_permission_authorized(self, admin_user):
        """Test IsAdmin permission with admin user"""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = admin_user
        
        permission = IsAdmin()
        
        assert permission.has_permission(request, None) is True
    
    def test_is_admin_permission_unauthorized(self, hr_user):
        """Test IsAdmin permission with non-admin user"""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = hr_user
        
        permission = IsAdmin()
        
        assert permission.has_permission(request, None) is False
    
    def test_is_admin_permission_unauthenticated(self):
        """Test IsAdmin permission with unauthenticated user"""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = None
        
        permission = IsAdmin()
        
        assert permission.has_permission(request, None) is False
    
    def test_is_admin_or_hr_permission_admin(self, admin_user):
        """Test IsAdminOrHR permission with admin user"""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = admin_user
        
        permission = IsAdminOrHR()
        
        assert permission.has_permission(request, None) is True
    
    def test_is_admin_or_hr_permission_hr(self, hr_user):
        """Test IsAdminOrHR permission with HR user"""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = hr_user
        
        permission = IsAdminOrHR()
        
        assert permission.has_permission(request, None) is True
    
    def test_is_admin_or_hr_permission_manager(self, manager_user):
        """Test IsAdminOrHR permission with manager user"""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = manager_user
        
        permission = IsAdminOrHR()
        
        assert permission.has_permission(request, None) is False
    
    def test_is_admin_or_hr_or_manager_permission_admin(self, admin_user):
        """Test IsAdminOrHROrManager permission with admin user"""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = admin_user
        
        permission = IsAdminOrHROrManager()
        
        assert permission.has_permission(request, None) is True
    
    def test_is_admin_or_hr_or_manager_permission_hr(self, hr_user):
        """Test IsAdminOrHROrManager permission with HR user"""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = hr_user
        
        permission = IsAdminOrHROrManager()
        
        assert permission.has_permission(request, None) is True
    
    def test_is_admin_or_hr_or_manager_permission_manager(self, manager_user):
        """Test IsAdminOrHROrManager permission with manager user"""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = manager_user
        
        permission = IsAdminOrHROrManager()
        
        assert permission.has_permission(request, None) is True
    
    def test_is_admin_or_hr_or_manager_permission_employee(self, employee_user):
        """Test IsAdminOrHROrManager permission with employee user"""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = employee_user
        
        permission = IsAdminOrHROrManager()
        
        assert permission.has_permission(request, None) is False