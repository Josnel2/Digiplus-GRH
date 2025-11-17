from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from .models import User, Employe, Poste

class PosteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poste
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

class EmployeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='user', 
        write_only=True,
        required=False
    )
    poste_details = PosteSerializer(source='poste', read_only=True)
    
    class Meta:
        model = Employe
        fields = '__all__'

class CreateEmployeSerializer(serializers.Serializer):
    # User fields
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default='employee')
    
    # Employe fields
    matricule = serializers.CharField(max_length=50)
    date_embauche = serializers.DateField()
    statut = serializers.ChoiceField(choices=Employe.STATUT_CHOICES, default='actif')
    adresse = serializers.CharField(required=False, allow_blank=True)
    poste_id = serializers.PrimaryKeyRelatedField(
        queryset=Poste.objects.all(), 
        required=False, 
        allow_null=True
    )
    telephone = serializers.CharField(required=False, allow_blank=True, max_length=20)
    date_naissance = serializers.DateField(required=False, allow_null=True)
    
    def create(self, validated_data):
        # Extract user data
        user_data = {
            'email': validated_data['email'],
            'password': make_password(validated_data['password']),
            'first_name': validated_data['first_name'],
            'last_name': validated_data['last_name'],
            'role': validated_data.get('role', 'employee')
        }
        
        # Create user
        user = User.objects.create(**user_data)
        
        # Create employe
        employe_data = {
            'user': user,
            'matricule': validated_data['matricule'],
            'date_embauche': validated_data['date_embauche'],
            'statut': validated_data.get('statut', 'actif'),
            'adresse': validated_data.get('adresse', ''),
            'poste': validated_data.get('poste_id'),
            'telephone': validated_data.get('telephone', ''),
            'date_naissance': validated_data.get('date_naissance')
        }
        
        employe = Employe.objects.create(**employe_data)
        return employe

class UpdateEmployeSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', required=False)
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    role = serializers.CharField(source='user.role', required=False)
    
    class Meta:
        model = Employe
        fields = [
            'matricule', 'date_embauche', 'statut', 'adresse', 'poste', 
            'telephone', 'date_naissance', 'email', 'first_name', 'last_name', 'role'
        ]
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        
        # Update employe fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update user fields
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()
        
        return instance