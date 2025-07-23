from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.permissions import AllowAny
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from apps.videos.views.video_creation_view import VideoCreationView
from apps.videos.views.video_crud_views import VideoUploadView
from apps.videos.views.avatar_list_view import AvatarListView

# 전체 경로를 위한 URL 패턴들 - 공통 경로 제거
api_urls = [
    path('api/v1/videos/generate', VideoCreationView.as_view(), name='video_generation'),
    path('api/v1/videos', VideoUploadView.as_view(), name='video-upload'),
    path('api/v1/videos/avatars', AvatarListView.as_view(), name='avatar-list'),
    path('api/v1/avatars', include('apps.avatars.urls')),
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
