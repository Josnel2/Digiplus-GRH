from rest_framework import status, generics, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from .models import OTP, Poste, Employe, DemandeConge, Notification
from rest_framework import generics, permissions
from .serializers import DemandeCongeSerializer, NotificationSerializer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .serializers import (
    # Authentication
    LoginSerializer, VerifyOTPSerializer, ResendOTPSerializer, ChangePasswordSerializer,
    # Profile
    UserProfileSerializer, UserProfileUpdateSerializer,
    # Admin Management
    SuperAdminCreateSerializer, AdminCreateSerializer, EmployeCreateSerializer, UserListSerializer,
    # Postes and Employes
    PosteSerializer, EmployeSerializer,DemandeCongeSerializer, NotificationSerializer
)
from .permissions import IsSuperAdmin, IsAdmin, IsAdminOrSuperAdmin, IsVerified
from .utils import send_otp_email, send_credentials_email

User = get_user_model()

def get_request_data(request):
    """Helper pour récupérer les données de la requête (POST ou GET)"""
    if request.method == 'GET':
        return request.query_params
    return request.data

# ==============================
# AUTHENTICATION VIEWS
# ==============================

@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Connexion avec email et mot de passe, puis envoi OTP
    """
    incoming_data = request.data if request.method == 'POST' else request.query_params
    if not incoming_data:
        incoming_data = request.query_params

    serializer = LoginSerializer(data=incoming_data)
    serializer.is_valid(raise_exception=True)
    
    email = serializer.validated_data["email"]
    password = serializer.validated_data["password"]
    
    # Authentifier l'utilisateur
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({
            'error': 'Email ou mot de passe incorrect.'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    if not user.check_password(password):
        return Response({
            'error': 'Email ou mot de passe incorrect.'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Envoyer l'OTP
    try:
        otp_code = send_otp_email(user)
        return Response({
            'message': 'Code OTP envoyé à votre email.',
            'email': user.email,
            'otp_code': otp_code  # À retirer en production
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': f'Erreur lors de l\'envoi du code OTP: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def verify_otp_view(request):
    """
    Vérification du code OTP et obtention des tokens JWT
    """
    incoming_data = request.data if request.method == 'POST' else request.query_params
    if not incoming_data:
        incoming_data = request.query_params

    serializer = VerifyOTPSerializer(data=incoming_data)
    serializer.is_valid(raise_exception=True)
    
    email = serializer.validated_data["email"]
    otp_code = serializer.validated_data["otp_code"]
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({
            'error': 'Utilisateur non trouvé.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Vérifier l'OTP
    try:
        otp = OTP.objects.filter(user=user, code=otp_code, is_used=False).latest("created_at")
    except OTP.DoesNotExist:
        return Response({
            'error': 'Code OTP invalide.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not otp.is_valid():
        return Response({
            'error': 'Code OTP expiré ou déjà utilisé.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Marquer l'OTP comme utilisé
    otp.is_used = True
    otp.save()
    
    # Marquer l'utilisateur comme vérifié
    if not user.is_verified:
        user.is_verified = True
        user.save()
    
    # Générer les tokens JWT
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'message': 'Connexion réussie.',
        'user': UserProfileSerializer(user).data,
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    }, status=status.HTTP_200_OK)

@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def resend_otp_view(request):
    """
    Renvoyer un code OTP
    """
    incoming_data = request.data if request.method == 'POST' else request.query_params
    if not incoming_data:
        incoming_data = request.query_params

    serializer = ResendOTPSerializer(data=incoming_data)
    serializer.is_valid(raise_exception=True)
    
    email = serializer.validated_data["email"]
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({
            'error': 'Utilisateur non trouvé.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        otp_code = send_otp_email(user)
        return Response({
            'message': 'Un nouveau code OTP a été envoyé.',
            'otp_code': otp_code  # À retirer en production
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': f'Erreur lors de l\'envoi du code OTP: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ==============================
# PROFILE VIEWS
# ==============================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile_view(request):
    """
    Obtenir le profil de l'utilisateur connecté
    """
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)

@api_view(['PUT', 'PATCH', 'POST'])
@permission_classes([IsAuthenticated])
def update_profile_view(request):
    """
    Modifier le profil de l'utilisateur connecté
    """
    user = request.user
    
    incoming_data = request.data if request.method in ['PUT', 'PATCH', 'POST'] else request.query_params
    if not incoming_data:
        incoming_data = request.query_params

    serializer = UserProfileUpdateSerializer(user, data=incoming_data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response(UserProfileSerializer(user).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST', 'PUT'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """
    Changer le mot de passe
    """
    user = request.user
    
    incoming_data = request.data if request.method in ['POST', 'PUT'] else request.query_params
    if not incoming_data:
        incoming_data = request.query_params

    serializer = ChangePasswordSerializer(data=incoming_data)
    
    if serializer.is_valid():
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({
                'error': 'Ancien mot de passe incorrect.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': 'Mot de passe changé avec succès.'})
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ==============================
# DASHBOARD VIEWS
# ==============================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOrSuperAdmin])
def admin_dashboard_data(request):
    """
    Données pour le dashboard admin
    """
    from django.db.models import Count, Q
    
    # Statistiques des utilisateurs
    total_users = User.objects.count()
    superadmins_count = User.objects.filter(is_superadmin=True).count()
    admins_count = User.objects.filter(is_admin=True, is_superadmin=False).count()
    employes_count = User.objects.filter(is_employe=True).count()
    verified_users = User.objects.filter(is_verified=True).count()
    
    # Statistiques des employés
    employes_stats = Employe.objects.aggregate(
        total=Count('id'),
        actifs=Count('id', filter=Q(statut='actif')),
        inactifs=Count('id', filter=Q(statut='inactif'))
    )
    
    # Statistiques des postes
    postes_count = Poste.objects.count()
    
    data = {
        'users': {
            'total': total_users,
            'superadmins': superadmins_count,
            'admins': admins_count,
            'employes': employes_count,
            'verified': verified_users,
            'unverified': total_users - verified_users,
        },
        'employes': employes_stats,
        'postes': postes_count,
        'recent_activity': {
            'last_login': request.user.last_login.strftime('%Y-%m-%d %H:%M:%S') if request.user.last_login else None,
            'current_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    }
    
    return Response(data)

# ==============================
# SUPER ADMIN MANAGEMENT VIEWS
# ==============================

class SuperAdminViewSet(viewsets.ModelViewSet):
    """
    Gestion des superadministrateurs
    Seul un superadmin peut gérer les superadmins
    """
    queryset = User.objects.filter(is_superadmin=True)
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = UserListSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SuperAdminCreateSerializer
        return UserListSerializer
    
    def create(self, request, *args, **kwargs):
        incoming_data = request.data if request.method == 'POST' else request.query_params
        if not incoming_data:
            incoming_data = request.query_params

        serializer = self.get_serializer(data=incoming_data)
        serializer.is_valid(raise_exception=True)
        
        password = incoming_data.get('password')
        user = serializer.save()
        
        # Envoyer les identifiants par email
        try:
            send_credentials_email(user, password)
        except Exception as e:
            # Ne pas supprimer l'utilisateur si l'email échoue
            pass
        
        return Response(
            UserListSerializer(user).data, 
            status=status.HTTP_201_CREATED
        )

# ==============================
# ADMIN MANAGEMENT VIEWS
# ==============================

class AdminViewSet(viewsets.ModelViewSet):
    """
    Gestion des administrateurs
    Seul un superadmin peut gérer les admins
    """
    queryset = User.objects.filter(is_admin=True, is_superadmin=False)
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = UserListSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AdminCreateSerializer
        return UserListSerializer
    
    def create(self, request, *args, **kwargs):
        incoming_data = request.data if request.method == 'POST' else request.query_params
        if not incoming_data:
            incoming_data = request.query_params

        serializer = self.get_serializer(data=incoming_data)
        serializer.is_valid(raise_exception=True)
        
        password = incoming_data.get('password')
        user = serializer.save()
        
        # Envoyer les identifiants par email
        try:
            send_credentials_email(user, password)
        except Exception as e:
            # Ne pas supprimer l'utilisateur si l'email échoue
            pass
        
        return Response(
            UserListSerializer(user).data, 
            status=status.HTTP_201_CREATED
        )

# ==============================
# EMPLOYE MANAGEMENT VIEWS
# ==============================

class EmployeViewSet(viewsets.ModelViewSet):
    """
    Gestion des employés
    Les superadmins et admins peuvent gérer les employés
    """
    queryset = User.objects.filter(is_employe=True)
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]
    serializer_class = UserListSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return EmployeCreateSerializer
        return UserListSerializer
    
    def create(self, request, *args, **kwargs):
        incoming_data = request.data if request.method == 'POST' else request.query_params
        if not incoming_data:
            incoming_data = request.query_params

        serializer = self.get_serializer(data=incoming_data)
        serializer.is_valid(raise_exception=True)
        
        password = incoming_data.get('password')
        user = serializer.save()
        
        # Envoyer les identifiants par email
        try:
            send_credentials_email(user, password)
        except Exception as e:
            # Ne pas supprimer l'utilisateur si l'email échoue
            pass
        
        return Response(
            UserListSerializer(user).data, 
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def toggle_verification(self, request, pk=None):
        """
        Activer/désactiver la vérification d'un employé
        """
        employe = self.get_object()
        employe.is_verified = not employe.is_verified
        employe.save()
        
        return Response({
            'message': f"Employé {'vérifié' if employe.is_verified else 'non vérifié'}.",
            'user': UserListSerializer(employe).data
        })

# ==============================
# POSTE MANAGEMENT VIEWS
# ==============================

class PosteViewSet(viewsets.ModelViewSet):
    """
    Gestion des postes
    """
    queryset = Poste.objects.all()
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]
    serializer_class = PosteSerializer

# ==============================
# EMPLOYE PROFILES VIEWS
# ==============================

class EmployeProfileViewSet(viewsets.ModelViewSet):
    """
    Gestion des profils employés
    """
    queryset = Employe.objects.select_related('user', 'poste').all()
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]
    serializer_class = EmployeSerializer
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Profil employé de l'utilisateur connecté
        """
        try:
            employe = Employe.objects.get(user=request.user)
            serializer = self.get_serializer(employe)
            return Response(serializer.data)
        except Employe.DoesNotExist:
            return Response(
                {'error': 'Profil employé non trouvé'}, 
                status=status.HTTP_404_NOT_FOUND
            )


channel_layer = get_channel_layer()

# ----------------------
# Vues Demande de congé
# ----------------------
class DemandeCongeListCreateView(generics.ListCreateAPIView):
    serializer_class = DemandeCongeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # L'employé voit seulement ses demandes
        return DemandeConge.objects.filter(employe__user=self.request.user)

    def perform_create(self, serializer):
        conge = serializer.save(employe=self.request.user.employe)
        # Envoi notification instantanée à l'admin ou superadmin
        async_to_sync(channel_layer.group_send)(
            "admins",  # Groupe admin (on créera le groupe dans le front/consumer)
            {
                "type": "send_notification",
                "content": {
                    "titre": "Nouvelle demande de congé",
                    "message": f"{conge.employe.user.get_full_name()} a demandé un {conge.type_conge} du {conge.date_debut} au {conge.date_fin}.",
                    "demande_id": conge.id,
                    "statut": conge.statut
                }
            }
        )

class DemandeCongeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = DemandeConge.objects.all()
    serializer_class = DemandeCongeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        old_instance = self.get_object()
        new_statut = serializer.validated_data.get('statut', old_instance.statut)
        
        # Extraire les champs additionnels modifiés (tous les champs du serializer sauf statut)
        extra_fields = {k: v for k, v in serializer.validated_data.items() if k != 'statut'}
        
        # Si le statut change vers 'approuve' ou 'rejete', utiliser les méthodes du modèle
        # pour garantir persistance de la Notification et envoi WebSocket cohérents.
        if old_instance.statut != new_statut:
            if new_statut == 'approuve':
                old_instance.approuver(**extra_fields)
                conge = old_instance
            elif new_statut == 'rejete':
                old_instance.rejeter(**extra_fields)
                conge = old_instance
            else:
                # Pour d'autres statuts, sauvegarder normalement et envoyer une notification générique
                conge = serializer.save()
                try:
                    async_to_sync(channel_layer.group_send)(
                        f"user_{conge.employe.user.id}",
                        {
                            "type": "send_notification",
                            "content": {
                                "titre": f"Demande {conge.statut}",
                                "message": f"Votre demande du {conge.date_debut} au {conge.date_fin} a été {conge.statut}.",
                                "demande_id": conge.id,
                                "statut": conge.statut,
                            }
                        }
                    )
                except Exception:
                    pass
        else:
            # Si statut ne change pas, sauvegarder les autres champs normalement
            conge = serializer.save()


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(demande_conge__employe__user=self.request.user).order_by('-date_envoi')
