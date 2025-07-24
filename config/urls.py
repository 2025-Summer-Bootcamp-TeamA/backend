from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.permissions import AllowAny
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from apps.videos.views.video_creation_view import VideoCreationView
from apps.videos.views.video_crud_views import VideoUploadView
from apps.videos.views.visionstory_latest_view import VisionStoryLatestVideoView
from apps.authentication.views import GoogleLoginView

# 전체 경로를 위한 URL 패턴들 - 공통 경로 제거
api_urls = [
    path('api/v1/videos/generate', VideoCreationView.as_view(), name='video_generation'),
    path('api/v1/videos/visionstory', VisionStoryLatestVideoView.as_view(), name='visionstory_latest'),
    path('api/v1/videos', VideoUploadView.as_view(), name='video-upload'),
    path('api/v1/avatars', include('apps.avatars.urls')),
    path('places/', include('apps.place.urls')),
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
        path('api/v1/videos', include('apps.videos.urls')),
        path('api/v1/avatars', include('apps.avatars.urls')),
        path('places/', include('apps.place.urls')),
        path('users/google/', GoogleLoginView.as_view()),  # 구글 OAuth 엔드포인트 Swagger에 포함
        path('', include('apps.authentication.urls')),
    ],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('places/', include('apps.place.urls')),
    path('users/google/', GoogleLoginView.as_view()),  # 구글 OAuth 엔드포인트 직접 연결
] + api_urls + [
    # Swagger API 문서
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/auth/', include('apps.authentication.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
