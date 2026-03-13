from rest_framework import serializers
from .models import CompanyDocument

class CompanyDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyDocument
        fields = ['id', 'title', 'file', 'uploaded_at', 'is_indexed']
        read_only_fields = ['id', 'uploaded_at', 'is_indexed']
