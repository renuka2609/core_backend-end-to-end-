from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)



urlpatterns = [
    path("", lambda request: JsonResponse({"status": "Core Backend API running"})),
    path("admin/", admin.site.urls),
    path('api/', include('vendors.urls')),
    path("api/", include("templates.urls")),
    path("api/responses/", include("responses.urls")),
    path("api/evidence/", include("evidence.urls")),
    

    

    # AUTH
    path("api/auth/", include("accounts.urls")),
    path('api/', include('reviews.urls')),
    path('api/', include('remediations.urls')),
    path('api/', include('dashboard.urls')),


    # SWAGGER
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
    path("api/", include("assessments.urls")),

]
static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)