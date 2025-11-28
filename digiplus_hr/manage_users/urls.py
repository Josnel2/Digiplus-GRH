from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from . import views

# Routers pour les ViewSets
router = DefaultRouter()
router.register(r'superadmins', views.SuperAdminViewSet, basename='superadmin')
router.register(r'admins', views.AdminViewSet, basename='admin')
router.register(r'employes', views.EmployeViewSet, basename='employe')
router.register(r'postes', views.PosteViewSet, basename='poste')
router.register(r'employe-profiles', views.EmployeProfileViewSet, basename='employe-profile')

urlpatterns = [
    # Authentification
    path('login', views.login_view, name='login'),
    path('verify-otp', views.verify_otp_view, name='verify_otp'),
    path('resend-otp', views.resend_otp_view, name='resend_otp'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Profil utilisateur
    path('profile', views.get_profile_view, name='profile'),
    path('profile/update', views.update_profile_view, name='update_profile'),
    path('change-password', views.change_password_view, name='change_password'),
    # Demandes de congé et notifications
    path('leaves/', views.DemandeCongeListCreateView.as_view(), name='demande-conge-list-create'),
    path('leaves/<int:pk>/', views.DemandeCongeDetailView.as_view(), name='demande-conge-detail'),
    path('mes-demandes/', views.EmployeDemandesListView.as_view(), name='employe-demandes-list'),
    path('notifications/', views.NotificationListView.as_view(), name='notifications-list'),
    path('notifications/<int:pk>/mark-read/', views.NotificationMarkAsReadView.as_view(), name='notification-mark-read'),

    # Routes de gestion (incluent les routers)
    path('', include(router.urls)),
    path('demandes/', views.AdminDemandesListView.as_view(), name='admin-demandes-list'),
    path('audit/', views.AdminAuditListView.as_view(), name='admin-audit-list'),
]