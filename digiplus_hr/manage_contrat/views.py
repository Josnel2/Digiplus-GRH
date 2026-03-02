from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from manage_users.permissions import IsAdminOrSuperAdmin
from .models import Formation, SessionFormation, DemandeFormation
from .serializers import FormationSerializer, SessionFormationSerializer, DemandeFormationSerializer


class FormationViewSet(viewsets.ModelViewSet):
    queryset = Formation.objects.all()
    serializer_class = FormationSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class SessionFormationViewSet(viewsets.ModelViewSet):
    queryset = SessionFormation.objects.select_related("formation").all()
    serializer_class = SessionFormationSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def enroll(self, request, pk=None):
        with transaction.atomic():
            session = SessionFormation.objects.select_for_update().get(pk=pk)

            if session.statut in ["cloturee", "annulee"]:
                return Response(
                    {"detail": "Les inscriptions sont fermées pour cette session."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Vérifie que l'utilisateur est rattaché à un employé
            employe = getattr(request.user, "employe", None)
            if not employe:
                return Response({"detail": "Aucun profil employé lié."}, status=status.HTTP_400_BAD_REQUEST)

            statut_initial = "en_attente"
            if session.places_restantes <= 0:
                statut_initial = "liste_attente"

            demande, created = DemandeFormation.objects.select_for_update().get_or_create(
                employe=employe,
                session=session,
                defaults={
                    "statut": statut_initial,
                    "created_by": request.user,
                },
            )

            if not created:
                return Response(
                    {"detail": "Une demande existe déjà pour cette session.", "statut": demande.statut},
                    status=status.HTTP_200_OK,
                )

        serializer = DemandeFormationSerializer(demande, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DemandeFormationViewSet(viewsets.ModelViewSet):
    queryset = DemandeFormation.objects.select_related("employe", "employe__user", "session", "session__formation")
    serializer_class = DemandeFormationSerializer

    def get_permissions(self):
        if self.action in ["approve", "reject", "destroy"]:
            permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.is_superadmin or user.is_admin:
            return self.queryset
        # Employé : ne voir que ses demandes
        employe = getattr(user, "employe", None)
        if employe:
            return self.queryset.filter(employe=employe)
        return DemandeFormation.objects.none()

    def perform_create(self, serializer):
        # Sécuriser l'employé: si l'utilisateur est un employé, forcer son profil
        employe = getattr(self.request.user, "employe", None)
        serializer.save(created_by=self.request.user, employe=employe)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdminOrSuperAdmin])
    def approve(self, request, pk=None):
        with transaction.atomic():
            demande = DemandeFormation.objects.select_for_update().select_related("session").get(pk=pk)
            session = SessionFormation.objects.select_for_update().get(pk=demande.session_id)

            if session.statut in ["cloturee", "annulee"]:
                return Response({"detail": "La session est clôturée ou annulée."}, status=status.HTTP_400_BAD_REQUEST)

            if session.places_restantes <= 0:
                demande.statut = "liste_attente"
            else:
                demande.statut = "confirme"

            demande.decided_by = request.user
            demande.save()

        return Response(DemandeFormationSerializer(demande, context={"request": request}).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdminOrSuperAdmin])
    def reject(self, request, pk=None):
        demande = self.get_object()
        demande.statut = "rejete"
        demande.motif = request.data.get("motif", demande.motif)
        demande.decided_by = request.user
        demande.save()
        return Response(DemandeFormationSerializer(demande, context={"request": request}).data)
