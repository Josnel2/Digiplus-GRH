from rest_framework import status, generics, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
import datetime
import uuid
import io
import qrcode
import hashlib
from django.core.files.base import ContentFile
from django.http import FileResponse
from .models import OTP, Departement, Poste, Employe, DemandeConge, Notification, DemandeCongeAudit, CodeQR, Badgeage, Presence
from rest_framework import generics, permissions
from .serializers import DemandeCongeSerializer, NotificationSerializer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .serializers import (
    # Authentication
    LoginSerializer, VerifyOTPSerializer, ResendOTPSerializer, ChangePasswordSerializer,
    ForgotPasswordRequestSerializer, ForgotPasswordVerifyOTPSerializer, ForgotPasswordResetSerializer,
    # Profile
    UserProfileSerializer, UserProfileUpdateSerializer,
    # Admin Management
    SuperAdminCreateSerializer, AdminCreateSerializer, EmployeCreateSerializer, UserListSerializer,
    # Postes and Employes
    DepartementSerializer, PosteSerializer, EmployeSerializer, DemandeCongeSerializer, NotificationSerializer,DemandeCongeAuditSerializer,
    CodeQRSerializer, BadgeageSerializer, PresenceSerializer, BadgeageScannerSerializer
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


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_request_view(request):
    """
    Étape 1: Envoi du code OTP pour réinitialisation
    """
    serializer = ForgotPasswordRequestSerializer(data=request.data)
    
    if serializer.is_valid():
        return Response({
            'message': 'Code de réinitialisation envoyé à votre email.',
            'email': serializer.validated_data['email'],
            'otp_code': serializer.validated_data.get('otp_code')  # À retirer en production
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_resend_otp_view(request):
    """
    Renvoyer le code OTP pour réinitialisation
    """
    serializer = ForgotPasswordRequestSerializer(data=request.data)
    
    if serializer.is_valid():
        return Response({
            'message': 'Code de réinitialisation renvoyé à votre email.',
            'email': serializer.validated_data['email'],
            'otp_code': serializer.validated_data.get('otp_code')  # À retirer en production
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_verify_otp_view(request):
    """
    Étape 2: Vérification du code OTP
    """
    serializer = ForgotPasswordVerifyOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    email = serializer.validated_data['email']
    otp_code = serializer.validated_data['otp_code']
    
    try:
        user = User.objects.get(email=email)
        otp = OTP.objects.filter(
            user=user,
            code=otp_code,
            is_used=False
        ).order_by('-created_at').first()
        
        if not otp:
            return Response({
                'error': 'Code OTP invalide ou expiré.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not otp.is_valid():
            return Response({
                'error': 'Code OTP expiré.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'message': 'Code OTP vérifié. Vous pouvez maintenant définir un nouveau mot de passe.',
            'email': email
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'error': 'Utilisateur non trouvé.'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_reset_view(request):
    """
    Étape 3: Réinitialisation du mot de passe
    """
    serializer = ForgotPasswordResetSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    email = serializer.validated_data['email']
    otp_code = serializer.validated_data['otp_code']
    new_password = serializer.validated_data['new_password']
    
    try:
        user = User.objects.get(email=email)
        otp = OTP.objects.filter(
            user=user,
            code=otp_code,
            is_used=False
        ).order_by('-created_at').first()
        
        if not otp or not otp.is_valid():
            return Response({
                'error': 'Code OTP invalide ou expiré.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Changer le mot de passe
        user.set_password(new_password)
        user.save()
        
        # Marquer l'OTP comme utilisé
        otp.is_used = True
        otp.save()
        
        return Response({
            'message': 'Mot de passe réinitialisé avec succès.'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'error': 'Utilisateur non trouvé.'
        }, status=status.HTTP_404_NOT_FOUND)
        
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


class DepartementViewSet(viewsets.ModelViewSet):
    """
    Gestion des départements
    """
    queryset = Departement.objects.all()
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]
    serializer_class = DepartementSerializer


class PosteViewSet(viewsets.ModelViewSet):
    """
    Gestion des postes
    """
    queryset = Poste.objects.select_related('departement').all()
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


class CodeQRViewSet(viewsets.ModelViewSet):
    queryset = CodeQR.objects.select_related('employe', 'employe__user').all()
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]
    serializer_class = CodeQRSerializer

    def _get_or_create_employe(self, target_user):
        try:
            return target_user.employe, False
        except Employe.DoesNotExist:
            if not getattr(target_user, 'is_employe', False):
                target_user.is_employe = True
                target_user.save(update_fields=['is_employe'])

            matricule = f"AUTO{target_user.id}-{uuid.uuid4().hex[:8].upper()}"
            while Employe.objects.filter(matricule=matricule).exists():
                matricule = f"AUTO{target_user.id}-{uuid.uuid4().hex[:8].upper()}"

            employe = Employe.objects.create(
                user=target_user,
                matricule=matricule,
                date_embauche=timezone.now().date(),
                statut='actif',
            )
            return employe, True

    def _ensure_qr_image(self, code_qr):
        if code_qr.qr_code_image:
            return

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(code_qr.code_unique)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        code_hash = hashlib.sha256(code_qr.code_unique.encode('utf-8')).hexdigest()[:16]
        filename = f"qr_{code_qr.employe_id}_{code_hash}.png"
        code_qr.qr_code_image.save(filename, ContentFile(buffer.read()), save=True)

    def perform_create(self, serializer):
        code_unique = serializer.validated_data.get('code_unique')
        if not code_unique:
            code_unique = CodeQR.generate_unique_code()
            while CodeQR.objects.filter(code_unique=code_unique).exists():
                code_unique = CodeQR.generate_unique_code()
        serializer.save(code_unique=code_unique)

    @action(detail=False, methods=['get'], url_path='me', permission_classes=[IsAuthenticated])
    def me(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': "Champ requis: 'user_id'."}, status=status.HTTP_400_BAD_REQUEST)

        if getattr(request.user, 'is_employe', False) and int(user_id) != int(request.user.id):
            return Response({'error': "Vous ne pouvez récupérer que votre propre QR."}, status=status.HTTP_403_FORBIDDEN)

        if not ((getattr(request.user, 'is_admin', False) or getattr(request.user, 'is_superadmin', False)) or int(user_id) == int(request.user.id)):
            return Response({'error': "Vous n'êtes pas autorisé à récupérer le QR de cet utilisateur."}, status=status.HTTP_403_FORBIDDEN)

        try:
            target_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        employe, created_profile = self._get_or_create_employe(target_user)

        code_qr = CodeQR.objects.filter(employe=employe, actif=True).order_by('-date_generation').first()
        if not code_qr:
            code_unique = CodeQR.generate_unique_code()
            while CodeQR.objects.filter(code_unique=code_unique).exists():
                code_unique = CodeQR.generate_unique_code()
            code_qr = CodeQR.objects.create(employe=employe, code_unique=code_unique, actif=True)

        self._ensure_qr_image(code_qr)

        data = CodeQRSerializer(code_qr).data
        if created_profile and int(target_user.id) == int(request.user.id):
            refresh = RefreshToken.for_user(target_user)
            data = {
                'code_qr': data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='me/regenerate', permission_classes=[IsAuthenticated])
    def regenerate(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': "Champ requis: 'user_id'."}, status=status.HTTP_400_BAD_REQUEST)

        if getattr(request.user, 'is_employe', False) and int(user_id) != int(request.user.id):
            return Response({'error': "Vous ne pouvez régénérer que votre propre QR."}, status=status.HTTP_403_FORBIDDEN)

        if not ((getattr(request.user, 'is_admin', False) or getattr(request.user, 'is_superadmin', False)) or int(user_id) == int(request.user.id)):
            return Response({'error': "Vous n'êtes pas autorisé à régénérer le QR de cet utilisateur."}, status=status.HTTP_403_FORBIDDEN)

        try:
            target_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        employe, created_profile = self._get_or_create_employe(target_user)

        CodeQR.objects.filter(employe=employe, actif=True).update(actif=False)
        code_unique = CodeQR.generate_unique_code()
        while CodeQR.objects.filter(code_unique=code_unique).exists():
            code_unique = CodeQR.generate_unique_code()
        code_qr = CodeQR.objects.create(employe=employe, code_unique=code_unique, actif=True)

        self._ensure_qr_image(code_qr)

        data = CodeQRSerializer(code_qr).data
        if created_profile and int(target_user.id) == int(request.user.id):
            refresh = RefreshToken.for_user(target_user)
            data = {
                'code_qr': data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='for-user', permission_classes=[IsAuthenticated, IsAdminOrSuperAdmin])
    def for_user(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': "Champ requis: 'user_id'."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        employe, _created_profile = self._get_or_create_employe(target_user)

        regenerate = bool(request.data.get('regenerate', True))
        if regenerate:
            CodeQR.objects.filter(employe=employe, actif=True).update(actif=False)

        code_qr = CodeQR.objects.filter(employe=employe, actif=True).order_by('-date_generation').first()
        if not code_qr:
            code_unique = CodeQR.generate_unique_code()
            while CodeQR.objects.filter(code_unique=code_unique).exists():
                code_unique = CodeQR.generate_unique_code()
            code_qr = CodeQR.objects.create(employe=employe, code_unique=code_unique, actif=True)

        self._ensure_qr_image(code_qr)

        return Response(CodeQRSerializer(code_qr).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='me/download', permission_classes=[IsAuthenticated])
    def download(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': "Champ requis: 'user_id'."}, status=status.HTTP_400_BAD_REQUEST)

        if getattr(request.user, 'is_employe', False) and int(user_id) != int(request.user.id):
            return Response({'error': "Vous ne pouvez télécharger que votre propre QR."}, status=status.HTTP_403_FORBIDDEN)

        if not ((getattr(request.user, 'is_admin', False) or getattr(request.user, 'is_superadmin', False)) or int(user_id) == int(request.user.id)):
            return Response({'error': "Vous n'êtes pas autorisé à télécharger le QR de cet utilisateur."}, status=status.HTTP_403_FORBIDDEN)

        try:
            target_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        employe, _created_profile = self._get_or_create_employe(target_user)
        code_qr = CodeQR.objects.filter(employe=employe, actif=True).order_by('-date_generation').first()
        if not code_qr:
            code_unique = CodeQR.generate_unique_code()
            while CodeQR.objects.filter(code_unique=code_unique).exists():
                code_unique = CodeQR.generate_unique_code()
            code_qr = CodeQR.objects.create(employe=employe, code_unique=code_unique, actif=True)

        self._ensure_qr_image(code_qr)

        if not code_qr.qr_code_image:
            return Response({'error': "Impossible de générer l'image du QR code."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response = FileResponse(code_qr.qr_code_image.open('rb'), content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="qr_{user_id}.png"'
        return response


class BadgeageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Badgeage.objects.select_related('employe', 'employe__user').all()
    permission_classes = [IsAuthenticated]
    serializer_class = BadgeageSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if getattr(self.request.user, 'is_employe', False):
            try:
                return qs.filter(employe=self.request.user.employe)
            except Employe.DoesNotExist:
                return qs.none()
        if getattr(self.request.user, 'is_admin', False) or getattr(self.request.user, 'is_superadmin', False):
            return qs
        return qs.none()

    @action(detail=False, methods=['post'], url_path='scanner', url_name='scanner')
    def scanner(self, request):
        serializer = BadgeageScannerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data['user_id']
        badge_type = serializer.validated_data['type']

        if getattr(request.user, 'is_employe', False) and int(user_id) != int(request.user.id):
            return Response({'error': "Vous ne pouvez pointer que pour votre propre compte."}, status=status.HTTP_403_FORBIDDEN)
        if not (getattr(request.user, 'is_employe', False) or getattr(request.user, 'is_admin', False) or getattr(request.user, 'is_superadmin', False)):
            return Response({'error': "Vous n'êtes pas autorisé à pointer."}, status=status.HTTP_403_FORBIDDEN)

        if not ((getattr(request.user, 'is_admin', False) or getattr(request.user, 'is_superadmin', False)) or int(user_id) == int(request.user.id)):
            return Response({'error': "Vous n'êtes pas autorisé à pointer pour cet utilisateur."}, status=status.HTTP_403_FORBIDDEN)

        try:
            target_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            employe = target_user.employe
        except Employe.DoesNotExist:
            return Response({'error': 'Profil employé non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()

        todays_badges = Badgeage.objects.filter(employe=employe, date=now.date()).order_by('datetime')
        has_arrivee = todays_badges.filter(type='arrivee').exists()
        has_depart = todays_badges.filter(type='depart').exists()
        pause_debut_count = todays_badges.filter(type='pause_debut').count()
        pause_fin_count = todays_badges.filter(type='pause_fin').count()
        pause_in_progress = pause_debut_count > pause_fin_count

        if badge_type == 'arrivee':
            if has_depart:
                return Response({'error': "Déjà pointé 'depart' aujourd'hui."}, status=status.HTTP_400_BAD_REQUEST)
            if has_arrivee:
                return Response({'error': "Déjà pointé 'arrivee' aujourd'hui."}, status=status.HTTP_400_BAD_REQUEST)

        if badge_type == 'pause_debut':
            if not has_arrivee:
                return Response({'error': "Impossible de commencer une pause avant l'arrivée."}, status=status.HTTP_400_BAD_REQUEST)
            if has_depart:
                return Response({'error': "Impossible de commencer une pause après le départ."}, status=status.HTTP_400_BAD_REQUEST)
            if pause_in_progress:
                return Response({'error': "Une pause est déjà en cours."}, status=status.HTTP_400_BAD_REQUEST)

        if badge_type == 'pause_fin':
            if not has_arrivee:
                return Response({'error': "Impossible de terminer une pause avant l'arrivée."}, status=status.HTTP_400_BAD_REQUEST)
            if has_depart:
                return Response({'error': "Impossible de terminer une pause après le départ."}, status=status.HTTP_400_BAD_REQUEST)
            if not pause_in_progress:
                return Response({'error': "Aucune pause en cours à terminer."}, status=status.HTTP_400_BAD_REQUEST)

        if badge_type == 'depart':
            if not has_arrivee:
                return Response({'error': "Impossible de pointer le départ avant l'arrivée."}, status=status.HTTP_400_BAD_REQUEST)
            if has_depart:
                return Response({'error': "Déjà pointé 'depart' aujourd'hui."}, status=status.HTTP_400_BAD_REQUEST)
            if pause_in_progress:
                return Response({'error': "Impossible de pointer le départ pendant une pause (terminez la pause)."}, status=status.HTTP_400_BAD_REQUEST)

        badgeage = Badgeage.objects.create(
            employe=employe,
            type=badge_type,
            localisation_latitude=serializer.validated_data.get('latitude'),
            localisation_longitude=serializer.validated_data.get('longitude'),
            device_info=serializer.validated_data.get('device_info'),
        )

        presence, _ = Presence.objects.get_or_create(
            employe=employe,
            date=now.date(),
            defaults={'statut': 'absent'},
        )

        if badge_type == 'arrivee':
            if presence.heure_arrivee is None:
                presence.heure_arrivee = now.time()
            presence.statut = 'present'

        if badge_type == 'pause_debut':
            presence.nb_pauses = (presence.nb_pauses or 0) + 1

        if badge_type == 'pause_fin':
            last_pause_start = Badgeage.objects.filter(
                employe=employe,
                date=now.date(),
                type='pause_debut',
                datetime__lte=badgeage.datetime,
            ).order_by('-datetime').first()
            if last_pause_start:
                delta = badgeage.datetime - last_pause_start.datetime
                added_minutes = max(0, int(delta.total_seconds() // 60))
                presence.duree_pauses_minutes = (presence.duree_pauses_minutes or 0) + added_minutes

        if badge_type == 'depart':
            presence.heure_depart = now.time()
            if presence.heure_arrivee is not None:
                arrivee_dt = timezone.make_aware(datetime.datetime.combine(now.date(), presence.heure_arrivee))
                depart_dt = timezone.make_aware(datetime.datetime.combine(now.date(), presence.heure_depart))
                total_minutes = max(0, int((depart_dt - arrivee_dt).total_seconds() // 60))
                pauses_minutes = int(presence.duree_pauses_minutes or 0)
                presence.duree_travail_minutes = max(0, total_minutes - pauses_minutes)
            presence.statut = 'present'

        presence.save()

        return Response(BadgeageSerializer(badgeage).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='jour-actuel', url_name='jour-actuel')
    def jour_actuel(self, request):
        today = timezone.now().date()
        qs = self.get_queryset().filter(date=today)
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(BadgeageSerializer(page, many=True).data)
        return Response(BadgeageSerializer(qs, many=True).data)


class PresenceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Presence.objects.select_related('employe', 'employe__user').all()
    permission_classes = [IsAuthenticated]
    serializer_class = PresenceSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if getattr(self.request.user, 'is_employe', False):
            try:
                return qs.filter(employe=self.request.user.employe)
            except Employe.DoesNotExist:
                return qs.none()
        if getattr(self.request.user, 'is_admin', False) or getattr(self.request.user, 'is_superadmin', False):
            return qs
        return qs.none()


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
                old_instance.approuver(admin=self.request.user, **extra_fields)
                conge = old_instance
            elif new_statut == 'rejete':
                old_instance.rejeter(admin=self.request.user, **extra_fields)
                conge = old_instance
            else:
                # Pour d'autres statuts, sauvegarder normalement et envoyer une notification générique
                conge = serializer.save()
                try:
                    channel_layer = get_channel_layer()
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


class AdminDemandesListView(generics.ListAPIView):
    """
    Endpoint pour les admins: voir TOUTES les demandes de congé
    GET /api/management/demandes/
    """
    serializer_class = DemandeCongeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Seulement les admins peuvent voir toutes les demandes
        if self.request.user.is_admin or self.request.user.is_superadmin:
            # Optionnel: filtrer par statut si ?statut=en_attente
            statut = self.request.query_params.get('statut', None)
            if statut:
                return DemandeConge.objects.filter(statut=statut).order_by('-created_at')
            return DemandeConge.objects.all().order_by('-created_at')
        
        # Sinon, vide
        return DemandeConge.objects.none()


class EmployeDemandesListView(generics.ListAPIView):
    """
    Endpoint pour les employés: voir ses propres demandes de congé
    GET /api/users/mes-demandes/
    """
    serializer_class = DemandeCongeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # L'employé voit seulement ses demandes
        if hasattr(self.request.user, 'employe'):
            return DemandeConge.objects.filter(employe__user=self.request.user).order_by('-created_at')
        return DemandeConge.objects.none()


class NotificationMarkAsReadView(generics.UpdateAPIView):
    """
    Endpoint pour marquer une notification comme lue
    PATCH /api/notifications/{id}/mark-read/
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'
    
    def get_queryset(self):
        # L'utilisateur peut marquer comme lue seulement ses propres notifications
        return Notification.objects.filter(demande_conge__employe__user=self.request.user)
    
    def partial_update(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.lu = True
        notification.save()
        
        serializer = self.get_serializer(notification)
        return Response({
            'status': 'success',
            'message': 'Notification marquée comme lue',
            'notification': serializer.data
        })


class AdminAuditListView(generics.ListAPIView):
    """
    Endpoint pour voir l'historique des approbations/rejets
    GET /api/management/audit/
    """
   
    serializer_class = DemandeCongeAuditSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Seulement les admins peuvent voir l'audit
        if self.request.user.is_admin or self.request.user.is_superadmin:
            return DemandeCongeAudit.objects.all().order_by('-date_action')
        return DemandeCongeAudit.objects.none()
