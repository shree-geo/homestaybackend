"""
Main URL Configuration for GrihaStay project
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger/OpenAPI Schema Configuration
schema_view = get_schema_view(
    openapi.Info(
        title="GrihaStay API",
        default_version='v1',
        description="""
# GrihaStay Property Management System API

A comprehensive multi-tenant property management system for homestays, hotels, and vacation rentals.

## Features
- Multi-tenant architecture with tenant isolation
- Property and room management
- Booking and reservation system
- Dynamic pricing and rate plans
- Inventory management
- Guest management
- Payment processing
- Media file handling with cleanup
- Location-based services with PostGIS

## Authentication
Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your-access-token>
```

Get your token from `/api/auth/login/` or `/api/auth/token/`

## Multi-tenancy
Each tenant has isolated data. The tenant is determined from the JWT token.

## Pagination
List endpoints support pagination with `?page=<page_number>` and `?page_size=<size>`

## Filtering
Most list endpoints support filtering, searching, and ordering. Check individual endpoint documentation.
        """,
        terms_of_service="https://www.grihastay.com/terms/",
        contact=openapi.Contact(email="support@grihastay.com"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    
    # Swagger/OpenAPI Documentation URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='api-root'),  # Root redirects to Swagger
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
