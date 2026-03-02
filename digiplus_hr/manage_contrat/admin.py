from django.contrib import admin
from .models import Formation, SessionFormation, DemandeFormation, Contrat


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ("titre", "format", "duree_heures", "actif", "created_at")
    search_fields = ("titre", "description", "objectifs")
    list_filter = ("format", "actif")
    ordering = ("titre",)


@admin.register(SessionFormation)
class SessionFormationAdmin(admin.ModelAdmin):
    list_display = ("formation", "date_debut", "date_fin", "capacite", "statut")
    list_filter = ("statut", "formation")
    search_fields = ("formation__titre", "lieu", "formateur")
    date_hierarchy = "date_debut"


@admin.register(DemandeFormation)
class DemandeFormationAdmin(admin.ModelAdmin):
    list_display = ("employe", "session", "statut", "created_at", "decided_by")
    list_filter = ("statut", "session__formation")
    search_fields = ("employe__matricule", "employe__user__email", "session__formation__titre")


@admin.register(Contrat)
class ContratAdmin(admin.ModelAdmin):
    list_display = ("reference", "employe", "type_contrat", "statut", "date_debut", "date_fin")
    list_filter = ("type_contrat", "statut", "devise")
    search_fields = ("reference", "employe__matricule", "employe__user__email")
    date_hierarchy = "date_debut"
