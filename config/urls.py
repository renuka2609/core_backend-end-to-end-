from django.urls import path, include
from django.http import JsonResponse

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

def root_view(request):
    return JsonResponse({
        "message": "AIDS Internship Core Backend API",
        "version": "1.0",
        "status": "running",
        "endpoints": {
            "docs": "/api/docs/",
            "schema": "/api/schema/",
            "accounts": "/api/accounts/"
        }
    })

urlpatterns = [
    path("", root_view),
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
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
]