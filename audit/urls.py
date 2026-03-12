"""
Audit App URLs

Routes for the immutable audit ledger API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditEventViewSet

router = DefaultRouter()
router.register(r'events', AuditEventViewSet, basename='audit-event')

app_name = 'audit'

urlpatterns = [
    path('', include(router.urls)),
]
