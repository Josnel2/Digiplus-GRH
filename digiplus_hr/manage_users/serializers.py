from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from .models import OTP, Departement, Poste, Employe, DemandeConge, Notification, DemandeCongeAudit, CodeQR, Badgeage, Presence


User = get_user_model()

# ==============================
# Authentication Serializers
# ==============================

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp_code = serializers.CharField(required=True, max_length=6)

class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

class ForgotPasswordRequestSerializer(serializers.Serializer):
    """Étape 1: Demande de réinitialisation"""
    email = serializers.EmailField()
    
    def validate(self, attrs):
        from .utils import send_otp_email
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        email = attrs.get('email')
        
        try:
            user = User.objects.get(email=email)
            
            # Supprimer les anciens OTP de cet utilisateur
            OTP.objects.filter(user=user, is_used=False).delete()
            
            # Générer et envoyer le nouveau OTP
            otp_code = send_otp_email(user, purpose='password_reset')
            
            # Stocker le code OTP dans attrs pour le retourner (dev only)
            attrs['otp_code'] = otp_code
            attrs['user'] = user
            
            return attrs
        except User.DoesNotExist:
            raise serializers.ValidationError("Aucun utilisateur trouvé avec cette adresse email.")

class ForgotPasswordVerifyOTPSerializer(serializers.Serializer):
    """Étape 2: Vérification OTP"""
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)
class ForgotPasswordResetSerializer(serializers.Serializer):
    """Étape 3: Nouveau mot de passe"""
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField()
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas")
        return data

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"new_password": "Les mots de passe ne correspondent pas."})
        return attrs


class BadgeageScannerSerializer(serializers.Serializer):
    code_qr = serializers.CharField(required=True)
    type = serializers.ChoiceField(choices=[
        ('arrivee', 'Arrivée'),
        ('depart', 'Départ'),
        ('pause_debut', 'Début de pause'),
        ('pause_fin', 'Fin de pause'),
    ])
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    device_info = serializers.CharField(required=False, allow_blank=True, allow_null=True)

# ==============================
# Profile Serializers
# ==============================

class UserProfileSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='get_role', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 
            'is_superadmin', 'is_admin', 'is_employe', 'is_verified',
            'role', 'created_at'
        ]
        read_only_fields = ['id', 'email', 'is_superadmin', 'is_admin', 'is_employe', 'is_verified', 'created_at']

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']

# ==============================
# Admin Management Serializers
# ==============================

class SuperAdminCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'confirm_password']

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        validated_data.update({
            'is_superadmin': True,
            'is_admin': False,
            'is_employe': False,
            'is_verified': True
        })
        user = User.objects.create_user(**validated_data)
        return user

class AdminCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'confirm_password']

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        validated_data.update({
            'is_superadmin': False,
            'is_admin': True,
            'is_employe': False,
            'is_verified': True
        })
        user = User.objects.create_user(**validated_data)
        return user

class EmployeCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    matricule = serializers.CharField(max_length=50, required=True)
    date_embauche = serializers.DateField(required=True)
    poste_id = serializers.PrimaryKeyRelatedField(queryset=Poste.objects.all(), required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'password', 'confirm_password',
            'matricule', 'date_embauche', 'poste_id'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        matricule = validated_data.pop('matricule')
        date_embauche = validated_data.pop('date_embauche')
        poste_id = validated_data.pop('poste_id', None)
        validated_data.pop('confirm_password')
        
        validated_data.update({
            'is_superadmin': False,
            'is_admin': False,
            'is_employe': True,
            'is_verified': True
        })
        
        user = User.objects.create_user(**validated_data)
        
        # Create employe profile
        Employe.objects.create(
            user=user,
            matricule=matricule,
            date_embauche=date_embauche,
            poste=poste_id
        )
        
        return user

class UserListSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='get_role', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 
            'is_superadmin', 'is_admin', 'is_employe', 'is_verified',
            'role', 'created_at'
        ]

# ==============================
# Departement Serializers
# ==============================

class DepartementSerializer(serializers.ModelSerializer):
    chef_info = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Departement
        fields = ['id', 'nom', 'description', 'chef_departement', 'chef_info', 'created_at', 'updated_at']
    
    def get_chef_info(self, obj):
        if obj.chef_departement:
            return {
                'id': obj.chef_departement.id,
                'name': obj.chef_departement.user.get_full_name(),
                'email': obj.chef_departement.user.email,
                'matricule': obj.chef_departement.matricule,
                'poste': obj.chef_departement.poste.titre if obj.chef_departement.poste else None
            }
        return None

# ==============================
# Poste Serializers
# ==============================

class PosteSerializer(serializers.ModelSerializer):
    departement_details = DepartementSerializer(source='departement', read_only=True)
    
    class Meta:
        model = Poste
        fields = ['id', 'titre', 'description', 'salaire_de_base', 'departement', 'departement_details', 'created_at', 'updated_at']

class EmployeSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    poste_details = PosteSerializer(source='poste', read_only=True)
    
    class Meta:
        model = Employe
        fields = '__all__'


class CodeQRSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeQR
        fields = '__all__'
        read_only_fields = ['code_unique', 'qr_code_image', 'date_generation']


class BadgeageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badgeage
        fields = '__all__'
        read_only_fields = ['datetime', 'date']


class PresenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Presence
        fields = '__all__'


class DemandeCongeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandeConge
        fields = '__all__'
        read_only_fields = ['employe', 'created_at', 'updated_at']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['demande_conge', 'date_envoi']

class DemandeCongeAuditSerializer(serializers.ModelSerializer):
    admin_name = serializers.CharField(source='admin.get_full_name', read_only=True)
    demande_info = serializers.SerializerMethodField()
    
    class Meta:
        model = DemandeCongeAudit
        fields = ['id', 'demande_conge', 'demande_info', 'admin', 'admin_name', 'action', 'raison', 'date_action']
        read_only_fields = ['id', 'date_action']
    
    def get_demande_info(self, obj):
        return {
            'id': obj.demande_conge.id,
            'employe': obj.demande_conge.employe.user.get_full_name(),
            'type': obj.demande_conge.type_conge,
            'date_debut': obj.demande_conge.date_debut,
            'date_fin': obj.demande_conge.date_fin,
        }
