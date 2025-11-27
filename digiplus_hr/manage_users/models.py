from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from datetime import timedelta
import random
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superadmin', True)
        extra_fields.setdefault('is_admin', False)
        extra_fields.setdefault('is_employe', False)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = None  # Remove username field
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    # Roles
    is_superadmin = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_employe = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = CustomUserManager()
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    @property
    def role(self):
        if self.is_superadmin:
            return 'superadmin'
        elif self.is_admin:
            return 'admin'
        else:
            return 'employe'

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    def is_valid(self):
        from django.conf import settings
        expiry_time = self.created_at + timedelta(minutes=getattr(settings, 'OTP_EXPIRY_MINUTES', 5))
        return timezone.now() < expiry_time and not self.is_used
    
    @staticmethod
    def generate_code():
        return str(random.randint(100000, 999999))
    
    def __str__(self):
        return f"OTP for {self.user.email} - {self.code}"
    
    class Meta:
        ordering = ['-created_at']

class Poste(models.Model):
    titre = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    salaire_de_base = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.titre

class Employe(models.Model):
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('suspendu', 'Suspendu'),
        ('congé', 'En congé'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employe')
    matricule = models.CharField(max_length=50, unique=True)
    date_embauche = models.DateField(default=timezone.now)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif')
    adresse = models.TextField(blank=True, null=True)
    poste = models.ForeignKey(Poste, on_delete=models.SET_NULL, null=True, blank=True, related_name='employes')
    telephone = models.CharField(max_length=20, blank=True, null=True)
    date_naissance = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.matricule} - {self.user.get_full_name()}"
    
class DemandeConge(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('approuve', 'Approuvé'),
        ('rejete', 'Rejeté'),
    ]

    TYPE_CONGE_CHOICES = [
        ('annuel', 'Congé annuel'),
        ('maladie', 'Congé maladie'),
        ('sans_solde', 'Congé sans solde'),
    ]

    employe = models.ForeignKey('Employe', on_delete=models.CASCADE, related_name='demandes_conge')
    type_conge = models.CharField(max_length=50, choices=TYPE_CONGE_CHOICES)
    date_debut = models.DateField()
    date_fin = models.DateField()
    description = models.TextField(blank=True, null=True)  # <-- Nouveau champ
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def approuver(self, **extra_fields):
        """Approuver la demande de congé et créer notification persistante + temps réel.
        
        Args:
            **extra_fields: champs additionnels à mettre à jour (ex: description)
        """
        self.statut = 'approuve'
        for key, value in extra_fields.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()
        
        Notification.objects.create(
            demande_conge=self,
            titre='Congé approuvé',
            message=f'Votre demande de congé du {self.date_debut} au {self.date_fin} a été approuvée.'
        )
        
        # Envoi notification temps réel via Channels au propriétaire
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{self.employe.user.id}",
                {
                    "type": "send_notification",
                    "content": {
                        "titre": "Congé approuvé",
                        "message": f"Votre demande du {self.date_debut} au {self.date_fin} a été approuvée.",
                        "demande_id": self.id,
                        "statut": self.statut,
                    }
                }
            )
        except Exception:
            # Ne pas faire échouer la logique principale si Channels n'est pas configuré
            pass

    def rejeter(self, **extra_fields):
        """Rejeter la demande de congé et créer notification persistante + temps réel.
        
        Args:
            **extra_fields: champs additionnels à mettre à jour (ex: description)
        """
        self.statut = 'rejete'
        for key, value in extra_fields.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()
        
        Notification.objects.create(
            demande_conge=self,
            titre='Congé rejeté',
            message=f'Votre demande de congé du {self.date_debut} au {self.date_fin} a été rejetée.'
        )
        
        # Envoi notification temps réel via Channels au propriétaire
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{self.employe.user.id}",
                {
                    "type": "send_notification",
                    "content": {
                        "titre": "Congé rejeté",
                        "message": f"Votre demande du {self.date_debut} au {self.date_fin} a été rejetée.",
                        "demande_id": self.id,
                        "statut": self.statut,
                    }
                }
            )
        except Exception:
            # Ne pas faire échouer la logique principale si Channels n'est pas configuré
            pass

    def __str__(self):
        return f"{self.employe.matricule} - {self.type_conge} ({self.statut})"
    

class Notification(models.Model):
    demande_conge = models.ForeignKey(DemandeConge, on_delete=models.CASCADE, related_name='notifications')
    titre = models.CharField(max_length=200)
    message = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification: {self.titre} pour {self.demande_conge.employe.matricule}"

