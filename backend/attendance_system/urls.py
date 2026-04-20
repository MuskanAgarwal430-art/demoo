from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path("admin/", admin.site.urls),

    # API docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # Auth
    path("api/v1/auth/", include("apps.authentication.urls")),

    # Users (admin management)
    path("api/v1/users/", include("apps.users.urls")),

    # Companies
    path("api/v1/companies/", include("core.urls")),

    # Per-company routes
    path("api/v1/<str:company_code>/", include("apps.attendance.urls")),
    path("api/v1/<str:company_code>/faces/", include("apps.faces.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
