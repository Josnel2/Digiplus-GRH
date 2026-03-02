from django.db import models
from django.contrib.auth import get_user_model
from manage_users.models import Employe

User = get_user_model()


class Formation(models.Model):
    FORMAT_CHOICES = [
        ("presentiel", "Présentiel"),
        ("distanciel", "Distanciel"),
        ("hybride", "Hybride"),
    ]

    titre = models.CharField(max_length=180, unique=True)
    description = models.TextField(blank=True, null=True)
    objectifs = models.TextField(blank=True, null=True)
    prerequis = models.TextField(blank=True, null=True)
    duree_heures = models.PositiveIntegerField(default=0)
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default="presentiel")
    cout = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    actif = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="formations_crees"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["titre"]

    def __str__(self):
        return self.titre


class SessionFormation(models.Model):
    STATUT_CHOICES = [
        ("planifiee", "Planifiée"),
        ("ouverte", "Ouverte aux inscriptions"),
        ("cloturee", "Clôturée"),
        ("annulee", "Annulée"),
    ]

    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="sessions")
    date_debut = models.DateField()
    date_fin = models.DateField()
    lieu = models.CharField(max_length=180, blank=True, null=True)
    capacite = models.PositiveIntegerField(default=0)
    formateur = models.CharField(max_length=180, blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="planifiee")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_debut"]
        indexes = [models.Index(fields=["formation", "date_debut"], name="session_formation_idx")]
        constraints = [
            models.CheckConstraint(
                check=models.Q(date_fin__gte=models.F("date_debut")),
                name="session_dates_coherentes",
            ),
            models.CheckConstraint(
                check=models.Q(capacite__gte=1),
                name="session_capacite_positive",
            ),
        ]

    def __str__(self):
        return f"{self.formation.titre} ({self.date_debut} - {self.date_fin})"

    @property
    def places_utilisees(self):
        """Nombre de places consommées par les inscriptions actives."""
        return self.inscriptions.filter(
            statut__in=["en_attente", "manager_valide", "rh_valide", "confirme"]
        ).count()

    @property
    def places_restantes(self):
        return max(self.capacite - self.places_utilisees, 0)


class DemandeFormation(models.Model):
    STATUT_CHOICES = [
        ("en_attente", "En attente validation manager"),
        ("manager_valide", "Validée manager"),
        ("rh_valide", "Validée RH"),
        ("confirme", "Confirmée"),
        ("liste_attente", "Liste d'attente"),
        ("rejete", "Rejetée"),
        ("annule", "Annulée"),
    ]

    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name="demandes_formation")
    session = models.ForeignKey(SessionFormation, on_delete=models.CASCADE, related_name="inscriptions")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="en_attente")
    motif = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="demandes_formation_creees"
    )
    decided_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="demandes_formation_decidees"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = (("employe", "session"),)
        indexes = [
            models.Index(fields=["session", "statut"], name="demande_session_statut_idx"),
        ]

    def __str__(self):
        return f"{self.employe.matricule} -> {self.session} [{self.statut}]"


class Contrat(models.Model):
    TYPE_CHOICES = [
        ("cdi", "CDI"),
        ("cdd", "CDD"),
        ("stage", "Stage"),
        ("prestation", "Prestation"),
    ]

    STATUT_CHOICES = [
        ("brouillon", "Brouillon"),
        ("en_signature", "En signature"),
        ("actif", "Actif"),
        ("suspendu", "Suspendu"),
        ("clos", "Clos"),
    ]

    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name="contrats")
    reference = models.CharField(max_length=80, unique=True)
    type_contrat = models.CharField(max_length=20, choices=TYPE_CHOICES)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="brouillon")
    poste = models.ForeignKey("manage_users.Poste", on_delete=models.SET_NULL, null=True, blank=True)
    lieu_travail = models.CharField(max_length=180, blank=True, null=True)
    date_debut = models.DateField()
    date_fin = models.DateField(blank=True, null=True)
    temps_travail_pct = models.PositiveIntegerField(default=100)
    salaire_base = models.DecimalField(max_digits=12, decimal_places=2)
    devise = models.CharField(max_length=8, default="XAF")
    periodicite = models.CharField(max_length=20, default="mensuel")
    horaire_hebdo_heures = models.PositiveIntegerField(default=40)
    conges_annuels_jours = models.PositiveIntegerField(default=30)
    periode_essai_mois = models.PositiveIntegerField(default=0)
    preavis_jours = models.PositiveIntegerField(default=0)
    avantages = models.TextField(blank=True, null=True)
    clauses_particulieres = models.TextField(blank=True, null=True)
    pdf_file = models.FileField(upload_to="contrats/", blank=True, null=True)

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="contrats_crees"
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="contrats_modifies"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["employe", "statut"], name="contrat_employe_statut_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(type_contrat__in=["cdd", "stage", "prestation"], date_fin__isnull=True),
                name="contrat_duree_daterange",
            ),
            models.CheckConstraint(
                check=models.Q(temps_travail_pct__gte=1, temps_travail_pct__lte=200),
                name="contrat_temps_travail_range",
            ),
        ]

    def __str__(self):
        return f"{self.reference} - {self.employe.matricule} ({self.get_type_contrat_display()})"
