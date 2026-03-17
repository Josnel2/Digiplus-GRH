from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from manage_users.models import Employe

from .ml_inference import absence_inference_service
from .models import CompanyDocument
from .serializers import CompanyDocumentSerializer
from .services import (
    analyze_performance_trends,
    ask_deepseek_chatbot,
    recommend_formations,
)

User = get_user_model()


class ChatbotAskView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Poser une question au Chatbot RH",
        request={
            "application/json": {
                "type": "object",
                "properties": {"question": {"type": "string"}},
                "required": ["question"],
            }
        },
        responses={200: {"type": "object", "properties": {"status": {"type": "string"}, "message": {"type": "string"}}}},
    )
    def post(self, request, *args, **kwargs):
        question = request.data.get("question")
        if not question:
            return Response({"detail": "La question est requise."}, status=status.HTTP_400_BAD_REQUEST)

        result = ask_deepseek_chatbot(request.user, question)
        return Response(result, status=status.HTTP_200_OK)


class RecommendFormationsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Obtenir des recommandations de formation personnalisees",
        responses={200: {"type": "object", "properties": {"status": {"type": "string"}, "recommendations": {"type": "string"}}}},
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        department = user.department.name if getattr(user, "department", None) else "Non specifie"
        role = user.role if hasattr(user, "role") else "Employe"

        user_profile_data = {
            "role": role,
            "department": department,
            "is_active": user.is_active,
            "email": user.email,
        }

        result = recommend_formations(user_profile_data)
        return Response(result, status=status.HTTP_200_OK)


class AdminTrendsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Generer une analyse IA des tendances de performance",
        responses={200: {"type": "object", "properties": {"status": {"type": "string"}, "analysis": {"type": "string"}}}},
    )
    def get(self, request, *args, **kwargs):
        if not getattr(request.user, "is_staff", False) and not getattr(request.user, "role", "") in ["admin", "manager"]:
            return Response({"detail": "Non autorise."}, status=status.HTTP_403_FORBIDDEN)

        users_data = {
            "total_employees": User.objects.count(),
            "active_employees": User.objects.filter(is_active=True).count(),
            "recent_absenteeism_rate": "12%",
            "average_delay_minutes": 15,
        }
        result = analyze_performance_trends(users_data)
        return Response(result, status=status.HTTP_200_OK)


class CompanyDocumentView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="Lister les documents de l'entreprise ou en charger un nouveau",
        request=CompanyDocumentSerializer,
        responses={200: CompanyDocumentSerializer(many=True), 201: CompanyDocumentSerializer},
    )
    def get(self, request, *args, **kwargs):
        docs = CompanyDocument.objects.all().order_by("-uploaded_at")
        serializer = CompanyDocumentSerializer(docs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Uploader un nouveau document PDF",
        request=CompanyDocumentSerializer,
        responses={201: CompanyDocumentSerializer},
    )
    def post(self, request, *args, **kwargs):
        if not getattr(request.user, "is_staff", False) and not getattr(request.user, "role", "") in ["admin", "manager"]:
            return Response({"detail": "Non autorise."}, status=status.HTTP_403_FORBIDDEN)

        serializer = CompanyDocumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompanyDocumentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Supprimer un document de la base IA", responses={204: None})
    def delete(self, request, pk, *args, **kwargs):
        if not getattr(request.user, "is_staff", False) and not getattr(request.user, "role", "") in ["admin", "manager"]:
            return Response({"detail": "Non autorise."}, status=status.HTTP_403_FORBIDDEN)

        try:
            doc = CompanyDocument.objects.get(pk=pk)
        except CompanyDocument.DoesNotExist:
            return Response({"detail": "Document non trouve."}, status=status.HTTP_404_NOT_FOUND)

        doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PredictAbsenceRetrieveView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Predire le risque d'absence ou de retard pour demain",
        responses={200: {"type": "object"}},
    )
    def get(self, request, *args, **kwargs):
        employe_id = request.query_params.get("employe_id")

        if employe_id:
            if not getattr(request.user, "is_staff", False) and not getattr(request.user, "role", "") in ["admin", "manager"]:
                return Response({"detail": "Non autorise."}, status=status.HTTP_403_FORBIDDEN)
            try:
                employe = Employe.objects.select_related("user", "poste", "poste__departement").get(pk=employe_id)
            except Employe.DoesNotExist:
                return Response({"detail": "Employe introuvable."}, status=status.HTTP_404_NOT_FOUND)
        else:
            try:
                employe = request.user.employe
            except Employe.DoesNotExist:
                return Response({"detail": "Profil employe introuvable."}, status=status.HTTP_404_NOT_FOUND)

        try:
            prediction = absence_inference_service.predict_for_employee(employe)
        except FileNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(prediction, status=status.HTTP_200_OK)


class DepartmentSummaryPredictionView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Predire le risque consolide d'absence ou de retard pour un departement",
        responses={200: {"type": "object"}},
    )
    def get(self, request, *args, **kwargs):
        if not getattr(request.user, "is_staff", False) and not getattr(request.user, "role", "") in ["admin", "manager"]:
            return Response({"detail": "Non autorise."}, status=status.HTTP_403_FORBIDDEN)

        departement_id = request.query_params.get("departement_id")
        if not departement_id:
            return Response({"detail": "Le parametre departement_id est requis."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            summary = absence_inference_service.predict_for_department(int(departement_id))
        except FileNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(summary, status=status.HTTP_200_OK)
