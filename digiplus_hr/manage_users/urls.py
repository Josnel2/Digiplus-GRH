from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'postes', views.PosteViewSet, basename='poste')
router.register(r'', views.EmployeViewSet, basename='employe')

urlpatterns = [
    path('', include(router.urls)),
]