from django.urls import path, include
from django.http import JsonResponse
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

from drf_spectacular.views import SpectacularAPIView
from rest_framework.permissions import AllowAny
from config.swagger_views import CustomSwaggerUIView

def root_view(request):
    return redirect('/api/docs/')
def home(request):
    return JsonResponse({
        "message": "Backend is running"
    })

urlpatterns = [
    path("", lambda request: redirect('/api/docs/')),
    path("api/", lambda request: JsonResponse({"status": "API running"})),
    path("api/accounts/", include("accounts.urls")),
    path("api/assessments/", include("assessments.urls")),
    path("api/responses/", include("responses.urls")),
    path("api/reviews/", include("reviews.urls")),
    path("api/evidence/", include("evidence.urls")),
    path("api/remediations/", include("remediations.urls")),
    path("api/audit/", include("audit.urls")),
    path("api/vendors/", include("vendors.urls")),
    path("api/templates/", include("templates.urls")),
    path("api/dashboard/", include("dashboard.urls")),
    path("api/schema/", SpectacularAPIView.as_view(permission_classes=[AllowAny]), name="schema"),
    path("api/docs/", CustomSwaggerUIView.as_view(), name="swagger-ui"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)