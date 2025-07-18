from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.permissions import AllowAny
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# 전체 경로를 위한 URL 패턴들 - 공통 경로 제거
api_urls = [
    path('api/v1/posts', include('apps.posts.urls')),
    path('api/v1/videos', include('apps.videos.urls')),
    path('api/v1/avatars', include('apps.avatars.urls')),
    path('docs/', include('apps.posts.urls')),  # 더미 경로로 공통 패턴 파괴
]

# Swagger 설정 - 전체 경로 표시용
schema_view = get_schema_view(
    openapi.Info(
        title="TeamA API",
        default_version='v1',
        description="TeamA Django REST API Documentation",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="team@example.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[AllowAny],
    patterns=[  # 실제 API만 포함
        path('api/v1/posts', include('apps.posts.urls')),
        path('api/v1/videos', include('apps.videos.urls')),
        path('api/v1/avatars', include('apps.avatars.urls')),
        path('api/auth/', include('apps.authentication.urls')),
    ],
)

urlpatterns = [
    path('admin/', admin.site.urls),
] + api_urls + [
    # Swagger API 문서
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),  # 루트에서도 Swagger 접근
    path('api/auth/', include('apps.authentication.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
