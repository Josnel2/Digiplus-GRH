from rest_framework.routers import DefaultRouter
from .views import FormationViewSet, SessionFormationViewSet, DemandeFormationViewSet

router = DefaultRouter()
router.register(r"formations", FormationViewSet, basename="formation")
router.register(r"sessions", SessionFormationViewSet, basename="session-formation")
router.register(r"inscriptions", DemandeFormationViewSet, basename="demande-formation")

urlpatterns = router.urls
