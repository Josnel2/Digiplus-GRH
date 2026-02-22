from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from . import views

# Routers pour les ViewSets
router = DefaultRouter()
router.register(r'superadmins', views.SuperAdminViewSet, basename='superadmin')
router.register(r'admins', views.AdminViewSet, basename='admin')
router.register(r'employes', views.EmployeViewSet, basename='employe')
router.register(r'departements', views.DepartementViewSet, basename='departement')
router.register(r'postes', views.PosteViewSet, basename='poste')
router.register(r'employe-profiles', views.EmployeProfileViewSet, basename='employe-profile')
router.register(r'code-qr', views.CodeQRViewSet, basename='code-qr')
router.register(r'badgeages', views.BadgeageViewSet, basename='badgeage')
router.register(r'presences', views.PresenceViewSet, basename='presence')

urlpatterns = [
    # Authentification
    path('login/', views.login_view, name='login'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Réinitialisation mot de passe
    path('forgot-password/request/', views.forgot_password_request_view, name='forgot-password-request'),
    path('forgot-password/resend-otp/', views.forgot_password_resend_otp_view, name='forgot-password-resend-otp'),
    path('forgot-password/verify-otp/', views.forgot_password_verify_otp_view, name='forgot-password-verify-otp'),
    path('forgot-password/reset/', views.forgot_password_reset_view, name='forgot-password-reset'),
    
    # Profil utilisateur
    path('profile/', views.get_profile_view, name='profile'),
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

    #formation
    path('formations/', views.FormationListCreateView.as_view(), name='formation-list-create'),
    path('formations/<int:pk>/', views.FormationDetailView.as_view(), name='formation-detail'),
]