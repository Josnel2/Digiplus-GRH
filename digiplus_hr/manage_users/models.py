from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from datetime import timedelta
import random
import secrets
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

class Departement(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    chef_departement = models.OneToOneField('Employe', on_delete=models.SET_NULL, null=True, blank=True, related_name='departement_manage')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.nom
    
    class Meta:
        ordering = ['nom']

class Poste(models.Model):
    titre = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    salaire_de_base = models.DecimalField(max_digits=10, decimal_places=2)
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, related_name='postes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.titre} ({self.departement.nom})"
    
    class Meta:
        ordering = ['departement', 'titre']

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

    def approuver(self, admin=None, raison='', **extra_fields):
        """Approuver la demande de congé et créer notification persistante + temps réel.
        
        Args:
            admin: L'utilisateur admin qui approuve (pour audit)
            raison: Raison optionnelle de l'approbation
            **extra_fields: champs additionnels à mettre à jour (ex: description)
        """
        self.statut = 'approuve'
        for key, value in extra_fields.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()
        
        # Créer notification pour l'employé
        Notification.objects.create(
            demande_conge=self,
            titre='Congé approuvé',
            message=f'Votre demande de congé du {self.date_debut} au {self.date_fin} a été approuvée.'
        )
        
        # Créer audit log
        if admin:
            DemandeCongeAudit.objects.create(
                demande_conge=self,
                admin=admin,
                action='approuve',
                raison=raison
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

    def rejeter(self, admin=None, raison='', **extra_fields):
        """Rejeter la demande de congé et créer notification persistante + temps réel.
        
        Args:
            admin: L'utilisateur admin qui rejette (pour audit)
            raison: Raison du rejet
            **extra_fields: champs additionnels à mettre à jour (ex: description)
        """
        self.statut = 'rejete'
        for key, value in extra_fields.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()
        
        # Créer notification pour l'employé
        message = f'Votre demande de congé du {self.date_debut} au {self.date_fin} a été rejetée.'
        if raison:
            message += f'\n\nRaison: {raison}'
        
        Notification.objects.create(
            demande_conge=self,
            titre='Congé rejeté',
            message=message
        )
        
        # Créer audit log
        if admin:
            DemandeCongeAudit.objects.create(
                demande_conge=self,
                admin=admin,
                action='rejete',
                raison=raison
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
                        "message": f"Votre demande du {self.date_debut} au {self.date_fin} a été rejetée." + (f"\n\nRaison: {raison}" if raison else ""),
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


class DemandeCongeAudit(models.Model):
    """Traçabilité des actions admin sur les demandes de congé"""
    ACTION_CHOICES = [
        ('approuve', 'Approuvée'),
        ('rejete', 'Rejetée'),
        ('modifiee', 'Modifiée'),
    ]
    
    demande_conge = models.ForeignKey(DemandeConge, on_delete=models.CASCADE, related_name='audit_logs')
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='demandes_audit')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    raison = models.TextField(blank=True, null=True)  # Raison du rejet
    date_action = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date_action']
    
    def __str__(self):
        return f"{self.demande_conge.employe.matricule} - {self.action} par {self.admin.email}"


class CodeQR(models.Model):
    code_unique = models.CharField(max_length=512, unique=True, db_index=True)
    qr_code_image = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    date_generation = models.DateTimeField(auto_now_add=True)
    date_expiration = models.DateField(blank=True, null=True)
    actif = models.BooleanField(default=True)
    employe = models.OneToOneField(Employe, on_delete=models.CASCADE, related_name='code_qr')

    class Meta:
        ordering = ['-date_generation']

    @staticmethod
    def generate_unique_code():
        return secrets.token_urlsafe(256)

    def __str__(self):
        return f"QR {self.employe.matricule} ({self.code_unique})"


class Badgeage(models.Model):
    TYPE_CHOICES = [
        ('arrivee', 'Arrivée'),
        ('depart', 'Départ'),
        ('pause_debut', 'Début de pause'),
        ('pause_fin', 'Fin de pause'),
    ]

    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='badgeages')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    datetime = models.DateTimeField(auto_now_add=True)
    date = models.DateField(auto_now_add=True, db_index=True)
    localisation_latitude = models.FloatField(blank=True, null=True)
    localisation_longitude = models.FloatField(blank=True, null=True)
    adresse_localisation = models.CharField(max_length=255, blank=True, null=True)
    device_info = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-datetime']
        indexes = [
            models.Index(fields=['employe', 'date'], name='mu_emp_date_bdg_idx'),
            models.Index(fields=['date'], name='manage_user_badge_date_idx'),
        ]

    def __str__(self):
        return f"{self.employe.matricule} - {self.type} - {self.datetime}"


class Presence(models.Model):
    STATUT_CHOICES = [
        ('present', 'Présent'),
        ('absent', 'Absent'),
        ('retard', 'En retard'),
        ('conge', 'Congé'),
        ('repos', 'Jour de repos'),
    ]

    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='presences')
    date = models.DateField(db_index=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='absent')
    heure_arrivee = models.TimeField(blank=True, null=True)
    heure_depart = models.TimeField(blank=True, null=True)
    duree_travail_minutes = models.IntegerField(default=0)
    nb_pauses = models.IntegerField(default=0)
    duree_pauses_minutes = models.IntegerField(default=0)
    remarques = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        unique_together = (('employe', 'date'),)
        indexes = [
            models.Index(fields=['employe', 'date'], name='manage_user_employe_date_idx'),
            models.Index(fields=['date', 'statut'], name='manage_user_date_statut_idx'),
        ]

    def __str__(self):
        return f"{self.employe.matricule} - {self.date} - {self.statut}"


class RapportPresence(models.Model):
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='rapports_presence')
    annee = models.IntegerField()
    mois = models.IntegerField()
    total_jours_travail = models.IntegerField(default=0)
    total_jours_present = models.IntegerField(default=0)
    total_jours_absent = models.IntegerField(default=0)
    total_jours_retard = models.IntegerField(default=0)
    total_jours_conge = models.IntegerField(default=0)
    total_jours_repos = models.IntegerField(default=0)
    total_heures_travail = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_heures_pauses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    observations = models.TextField(blank=True, null=True)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-annee', '-mois']
        unique_together = (('employe', 'annee', 'mois'),)
        indexes = [
            models.Index(fields=['employe', 'annee', 'mois'], name='manage_user_rapport_idx'),
        ]

    def __str__(self):
        return f"{self.employe.matricule} - {self.mois}/{self.annee}"


class Formation(models.Model):
    titre = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    date_debut = models.DateField()
    date_fin = models.DateField()
    formateur = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.titre
    

