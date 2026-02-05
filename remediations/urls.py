from rest_framework.routers import DefaultRouter
from .views import RemediationViewSet

router = DefaultRouter()
router.register(r'remediations', RemediationViewSet, basename='remediations')

urlpatterns = router.urls
