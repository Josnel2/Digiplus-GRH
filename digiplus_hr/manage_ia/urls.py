from django.urls import path

from .views import (
    AdminTrendsView,
    ChatbotAskView,
    CompanyDocumentDetailView,
    CompanyDocumentView,
    DepartmentSummaryPredictionView,
    PredictAbsenceRetrieveView,
    RecommendFormationsView,
)

urlpatterns = [
    path("chatbot/ask/", ChatbotAskView.as_view(), name="chatbot_ask"),
    path("recommendations/me/", RecommendFormationsView.as_view(), name="recommend_formations"),
    path("admin/trends/", AdminTrendsView.as_view(), name="admin_trends"),
    path("documents/", CompanyDocumentView.as_view(), name="company_documents"),
    path("documents/<int:pk>/", CompanyDocumentDetailView.as_view(), name="company_document_detail"),
    path("predict/absences/", PredictAbsenceRetrieveView.as_view(), name="predict_absence"),
    path("predict/department-summary/", DepartmentSummaryPredictionView.as_view(), name="predict_department_summary"),
]
