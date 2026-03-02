from rest_framework import serializers
from manage_users.models import Employe
from .models import Formation, SessionFormation, DemandeFormation


class FormationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Formation
        fields = [
            "id",
            "titre",
            "description",
            "objectifs",
            "prerequis",
            "duree_heures",
            "format",
            "cout",
            "actif",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "created_at", "updated_at")


class SessionFormationSerializer(serializers.ModelSerializer):
    formation = FormationSerializer(read_only=True)
    formation_id = serializers.PrimaryKeyRelatedField(
        source="formation", queryset=Formation.objects.all(), write_only=True
    )
    places_restantes = serializers.IntegerField(read_only=True)
    places_utilisees = serializers.IntegerField(read_only=True)

    class Meta:
        model = SessionFormation
        fields = [
            "id",
            "formation",
            "formation_id",
            "date_debut",
            "date_fin",
            "lieu",
            "capacite",
            "formateur",
            "statut",
            "places_restantes",
            "places_utilisees",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "places_restantes", "places_utilisees", "created_at", "updated_at")

    def validate(self, attrs):
        data = {**getattr(self.instance, "__dict__", {}), **attrs}
        date_debut = data.get("date_debut")
        date_fin = data.get("date_fin")
        capacite = data.get("capacite")

        errors = {}
        if date_debut and date_fin and date_fin < date_debut:
            errors["date_fin"] = "La date de fin doit être postérieure ou égale à la date de début."
        if capacite is not None and capacite < 1:
            errors["capacite"] = "La capacité doit être supérieure ou égale à 1."

        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class DemandeFormationSerializer(serializers.ModelSerializer):
    session = SessionFormationSerializer(read_only=True)
    session_id = serializers.PrimaryKeyRelatedField(
        source="session", queryset=SessionFormation.objects.all(), write_only=True
    )
    employe_id = serializers.PrimaryKeyRelatedField(
        source="employe", queryset=Employe.objects.all(), write_only=True, required=False
    )

    class Meta:
        model = DemandeFormation
        fields = [
            "id",
            "employe",
            "employe_id",
            "session",
            "session_id",
            "statut",
            "motif",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "employe", "statut", "created_at", "updated_at")

    def create(self, validated_data):
        # Employé injecté depuis la vue si non fourni (employé connecté)
        if not validated_data.get("employe"):
            request = self.context.get("request")
            if request and hasattr(request.user, "employe"):
                validated_data["employe"] = request.user.employe
        return super().create(validated_data)

    def validate(self, attrs):
        session = attrs.get("session")
        if session and session.statut in ["cloturee", "annulee"]:
            raise serializers.ValidationError("Les inscriptions sont fermées pour cette session.")
        return attrs
