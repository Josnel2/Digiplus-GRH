from django.db import transaction
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from manage_users.permissions import IsAdminOrSuperAdmin
from .models import Formation, SessionFormation, DemandeFormation, Contrat
from .serializers import (
    FormationSerializer,
    SessionFormationSerializer,
    DemandeFormationSerializer,
    ContratSerializer,
)
import io
import datetime


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


class ContratViewSet(viewsets.ModelViewSet):
    queryset = Contrat.objects.select_related("employe", "employe__user", "poste")
    serializer_class = ContratSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy", "export_pdf"]:
            permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        qs = self.queryset
        if user.is_superadmin or user.is_admin:
            return qs
        employe = getattr(user, "employe", None)
        if employe:
            return qs.filter(employe=employe)
        return Contrat.objects.none()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=["get"])
    def export_pdf(self, request, pk=None):
        contrat = self.get_object()

        def clean(text: str) -> str:
            # Supprimer/normaliser les accents pour éviter la corruption d'encodage en PDF minimal
            import unicodedata

            return (
                unicodedata.normalize("NFKD", text or "")
                .encode("ascii", "ignore")
                .decode("ascii")
                .replace("\\", "\\\\")
                .replace("(", "\\(")
                .replace(")", "\\)")
            )

        def build_pdf(title: str, rows):
            """PDF 1.4 minimaliste mais mise en page plus soignée (panneau gris, titres, colonnes)."""
            buf = io.BytesIO()
            objects = []

            # 1 Catalog
            objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
            # 2 Pages
            objects.append("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
            # 3 Page
            objects.append(
                "3 0 obj\n"
                "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
                "/Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> >>\n"
                "endobj\n"
            )

            # Content stream assembly
            content = []
            margin = 40
            width = 595
            height = 842
            line = 16
            start_y = height - margin

            # Panel background
            rect_height = (len(rows) + 4) * line + 30
            rect_y = start_y - rect_height + 10
            content.append("q")
            content.append("0.95 g")
            content.append(f"{margin} {rect_y:.1f} {width-2*margin} {rect_height:.1f} re f")
            content.append("Q")

            y = start_y - 20
            content.append("BT")
            # Title
            content.append("/F2 14 Tf")
            content.append(f"1 0 0 1 {margin+10} {y} Tm")
            content.append(f"({clean(title)}) Tj")

            # Body
            y -= 22
            content.append("/F1 10 Tf")
            for label, value in rows:
                content.append(f"1 0 0 1 {margin+10} {y} Tm")
                content.append(f"({clean(label)} : ) Tj")
                content.append(f"({clean(value)}) Tj")
                y -= line
                if y < margin:
                    # Simple single-page doc; break if overflow
                    break
            content.append("ET")

            content_stream = "\n".join(content).encode("latin-1")
            objects.append(
                f"4 0 obj\n<< /Length {len(content_stream)} >>\nstream\n".encode("latin-1")
                + content_stream
                + b"\nendstream\nendobj\n"
            )

            # 5 Font regular
            objects.append("5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")
            # 6 Font bold
            objects.append("6 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj\n")

            # Assemble with xref
            offsets = []
            buf.write(b"%PDF-1.4\n")
            for obj in objects:
                offsets.append(buf.tell())
                if isinstance(obj, bytes):
                    buf.write(obj)
                else:
                    buf.write(obj.encode("latin-1"))
            xref_pos = buf.tell()
            buf.write(f"xref\n0 {len(objects)+1}\n".encode("latin-1"))
            buf.write(b"0000000000 65535 f \n")
            for off in offsets:
                buf.write(f"{off:010d} 00000 n \n".encode("latin-1"))
            buf.write(
                f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode(
                    "latin-1"
                )
            )
            buf.seek(0)
            return buf.getvalue()

        rows = [
            ("Employe", f"{contrat.employe.user.get_full_name()} ({contrat.employe.matricule})"),
            ("Poste", contrat.poste.titre if contrat.poste else "N/A"),
            ("Lieu de travail", contrat.lieu_travail or "N/A"),
            ("Type", contrat.get_type_contrat_display()),
            ("Statut", contrat.get_statut_display()),
            ("Date debut", str(contrat.date_debut)),
            ("Date fin", str(contrat.date_fin) if contrat.date_fin else "N/A"),
            ("Temps de travail", f"{contrat.temps_travail_pct}%"),
            ("Salaire base", f"{contrat.salaire_base} {contrat.devise} ({contrat.periodicite})"),
            ("Horaire hebdo", f"{contrat.horaire_hebdo_heures} h"),
            ("Conges annuels", f"{contrat.conges_annuels_jours} jours"),
            ("Periode d'essai", f"{contrat.periode_essai_mois} mois"),
            ("Preavis", f"{contrat.preavis_jours} jours"),
            ("Avantages", contrat.avantages or "N/A"),
            ("Clauses particulieres", contrat.clauses_particulieres or "N/A"),
            ("Genere le", datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")),
        ]

        pdf_bytes = build_pdf(f"Contrat {contrat.reference}", rows)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename=\"contrat_{contrat.reference}.pdf\"'
        return response

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdminOrSuperAdmin])
    def reject(self, request, pk=None):
        demande = self.get_object()
        demande.statut = "rejete"
        demande.motif = request.data.get("motif", demande.motif)
        demande.decided_by = request.user
        demande.save()
        return Response(DemandeFormationSerializer(demande, context={"request": request}).data)
