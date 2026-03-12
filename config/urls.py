from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.conf import settings
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from accounts.views import LogoutView
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
    path("api/audit/", include("audit.urls")),
    

    

    # AUTH
    path("api/auth/", include("accounts.urls")),
    path('api/', include('reviews.urls')),
    path('api/', include('remediations.urls')),
    path('api/', include('dashboard.urls')),
     path('admin/', admin.site.urls),

    path('api/login/', TokenObtainPairView.as_view(), name='login'),
    path('api/refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('api/logout/', LogoutView.as_view(), name='logout'),


    # SWAGGER
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
    path("api/", include("assessments.urls")),

]
static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)