from rest_framework.routers import DefaultRouter
from .views import FormationViewSet, SessionFormationViewSet, DemandeFormationViewSet, ContratViewSet

router = DefaultRouter()
router.register(r"formations", FormationViewSet, basename="formation")
router.register(r"sessions", SessionFormationViewSet, basename="session-formation")
router.register(r"inscriptions", DemandeFormationViewSet, basename="demande-formation")
router.register(r"contracts", ContratViewSet, basename="contrat")

urlpatterns = router.urls
