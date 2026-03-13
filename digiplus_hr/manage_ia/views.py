from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiExample
from .services import ask_deepseek_chatbot, analyze_performance_trends, recommend_formations

from rest_framework.parsers import MultiPartParser, FormParser
from .models import CompanyDocument
from .serializers import CompanyDocumentSerializer

User = get_user_model()

class ChatbotAskView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Poser une question au Chatbot RH",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"}
                },
                "required": ["question"]
            }
        },
        responses={200: {"type": "object", "properties": {"status": {"type": "string"}, "message": {"type": "string"}}}}
    )
    def post(self, request, *args, **kwargs):
        question = request.data.get('question')
        if not question:
            return Response({"detail": "La question est requise."}, status=status.HTTP_400_BAD_REQUEST)
        
        result = ask_deepseek_chatbot(request.user, question)
        return Response(result, status=status.HTTP_200_OK)


class RecommendFormationsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Obtenir des recommandations de formation personnalisées",
        responses={200: {"type": "object", "properties": {"status": {"type": "string"}, "recommendations": {"type": "string"}}}}
    )
    def get(self, request, *args, **kwargs):
        # Compiler les infos utiles
        user = request.user
        department = user.department.name if getattr(user, 'department', None) else "Non spécifié"
        role = user.role if hasattr(user, 'role') else "Employé"
        
        user_profile_data = {
            "role": role,
            "department": department,
            "is_active": user.is_active,
            "email": user.email
        }
        
        result = recommend_formations(user_profile_data)
        return Response(result, status=status.HTTP_200_OK)


class AdminTrendsView(APIView):
    # Idéalement IsAdminUser, mais testons avec IsAuthenticated selon vos permissions
    permission_classes = [IsAuthenticated] 

    @extend_schema(
        summary="Générer une analyse IA des tendances de performance (Admin)",
        responses={200: {"type": "object", "properties": {"status": {"type": "string"}, "analysis": {"type": "string"}}}}
    )
    def get(self, request, *args, **kwargs):
        if not getattr(request.user, 'is_staff', False) and not getattr(request.user, 'role', '') in ['admin', 'manager']:
            return Response({"detail": "Non autorisé."}, status=status.HTTP_403_FORBIDDEN)
            
        # Simuler ou récupérer des données agrégées (ex: compte d'utilisateurs actifs, départs, etc.)
        # Dans un cas réel, vous query_set des données de Présences/Absences
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        
        users_data = {
            "total_employees": total_users,
            "active_employees": active_users,
            "recent_absenteeism_rate": "12%", # fake data pour la démo
            "average_delay_minutes": 15
        }
        
        result = analyze_performance_trends(users_data)
        return Response(result, status=status.HTTP_200_OK)


class CompanyDocumentView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="Lister tous les documents de l'entreprise ou en charger un nouveau",
        request=CompanyDocumentSerializer,
        responses={200: CompanyDocumentSerializer(many=True), 201: CompanyDocumentSerializer}
    )
    def get(self, request, *args, **kwargs):
        # Lister tous les documents
        docs = CompanyDocument.objects.all().order_by('-uploaded_at')
        serializer = CompanyDocumentSerializer(docs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Uploader un nouveau document (PDF)",
        request=CompanyDocumentSerializer,
        responses={201: CompanyDocumentSerializer}
    )
    def post(self, request, *args, **kwargs):
        # Restreindre l'upload aux admins si nécessaire
        if not getattr(request.user, 'is_staff', False) and not getattr(request.user, 'role', '') in ['admin', 'manager']:
            return Response({"detail": "Non autorisé."}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = CompanyDocumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompanyDocumentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Supprimer un document de la base IA",
        responses={204: None}
    )
    def delete(self, request, pk, *args, **kwargs):
        # Restreindre la suppression aux admins
        if not getattr(request.user, 'is_staff', False) and not getattr(request.user, 'role', '') in ['admin', 'manager']:
            return Response({"detail": "Non autorisé."}, status=status.HTTP_403_FORBIDDEN)
            
        try:
            doc = CompanyDocument.objects.get(pk=pk)
            doc.delete() # Le signal post_delete supprimera le fichier physique
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CompanyDocument.DoesNotExist:
            return Response({"detail": "Document non trouvé."}, status=status.HTTP_404_NOT_FOUND)
