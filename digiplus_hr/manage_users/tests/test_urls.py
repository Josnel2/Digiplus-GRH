import pytest
from django.urls import reverse, resolve
from manage_users.views import PosteViewSet, EmployeViewSet

class TestUrls:
    """Tests for URL routing"""
    
    def test_poste_list_url(self):
        """Test poste list URL"""
        url = reverse('poste-list')
        assert url == '/api/employees/postes/'
        
        resolver = resolve('/api/employees/postes/')
        assert resolver.func.cls == PosteViewSet
    
    def test_poste_detail_url(self):
        """Test poste detail URL"""
        url = reverse('poste-detail', kwargs={'pk': 1})
        assert url == '/api/employees/postes/1/'
    
    def test_employe_list_url(self):
        """Test employe list URL"""
        url = reverse('employe-list')
        assert url == '/api/employees/'
        
        resolver = resolve('/api/employees/')
        assert resolver.func.cls == EmployeViewSet
    
    def test_employe_detail_url(self):
        """Test employe detail URL"""
        url = reverse('employe-detail', kwargs={'pk': 1})
        assert url == '/api/employees/1/'
    
    def test_employe_activate_url(self):
        """Test employe activate URL"""
        url = reverse('employe-activate', kwargs={'pk': 1})
        assert url == '/api/employees/1/activate/'
    
    def test_employe_me_url(self):
        """Test employe me URL"""
        url = reverse('employe-me')
        assert url == '/api/employees/me/'