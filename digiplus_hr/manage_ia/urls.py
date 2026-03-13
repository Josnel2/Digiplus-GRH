from django.urls import path
from .views import ChatbotAskView, RecommendFormationsView, AdminTrendsView, CompanyDocumentView, CompanyDocumentDetailView

urlpatterns = [
    path('chatbot/ask/', ChatbotAskView.as_view(), name='chatbot_ask'),
    path('recommendations/me/', RecommendFormationsView.as_view(), name='recommend_formations'),
    path('admin/trends/', AdminTrendsView.as_view(), name='admin_trends'),
    path('documents/', CompanyDocumentView.as_view(), name='company_documents'),
    path('documents/<int:pk>/', CompanyDocumentDetailView.as_view(), name='company_document_detail'),
]
