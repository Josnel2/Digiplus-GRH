from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import User, Employe, Poste
from .serializers import (
    EmployeSerializer, 
    CreateEmployeSerializer, 
    UpdateEmployeSerializer,
    PosteSerializer
)
from .permissions import IsAdmin, IsSuperAdmin

class PosteViewSet(viewsets.ModelViewSet):
    queryset = Poste.objects.all()
    serializer_class = PosteSerializer
    permission_classes = [IsAdmin]

class EmployeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]
    
    def get_queryset(self):
        return Employe.objects.select_related('user', 'poste').all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateEmployeSerializer
        elif self.action in ['update', 'partial_update']:
            return UpdateEmployeSerializer
        return EmployeSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employe = serializer.save()
        
        # Return the created employe with full details
        employe_serializer = EmployeSerializer(employe)
        return Response(employe_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        employe = serializer.save()
        
        employe_serializer = EmployeSerializer(employe)
        return Response(employe_serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Soft delete: disable the user instead of deleting
        user = instance.user
        user.is_active = False
        user.save()
        
        # Optionally, you can also mark the employe as inactive
        instance.statut = 'inactif'
        instance.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def activate(self, request, pk=None):
        employe = self.get_object()
        user = employe.user
        user.is_active = True
        user.save()
        
        employe.statut = 'actif'
        employe.save()
        
        return Response({'status': 'Employé activé'})
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's employe profile"""
        try:
            employe = Employe.objects.get(user=request.user)
            serializer = self.get_serializer(employe)
            return Response(serializer.data)
        except Employe.DoesNotExist:
            return Response(
                {'error': 'Profil employé non trouvé'}, 
                status=status.HTTP_404_NOT_FOUND
            )