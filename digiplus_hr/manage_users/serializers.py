from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from .models import OTP, Poste, Employe, DemandeConge, Notification

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

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"new_password": "Les mots de passe ne correspondent pas."})
        return attrs

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
# Poste Serializers
# ==============================

class PosteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poste
        fields = '__all__'

class EmployeSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    poste_details = PosteSerializer(source='poste', read_only=True)
    
    class Meta:
        model = Employe
        fields = '__all__'

    from rest_framework import serializers
from .models import DemandeConge, Notification

class DemandeCongeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandeConge
        fields = '__all__'
        read_only_fields = ['employe', 'statut', 'created_at', 'updated_at']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['demande_conge', 'date_envoi', 'lu']
