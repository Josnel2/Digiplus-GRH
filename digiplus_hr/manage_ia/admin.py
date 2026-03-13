from django.contrib import admin
from .models import CompanyDocument

@admin.register(CompanyDocument)
class CompanyDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_at', 'is_indexed')
    list_filter = ('is_indexed', 'uploaded_at')
    search_fields = ('title',)
