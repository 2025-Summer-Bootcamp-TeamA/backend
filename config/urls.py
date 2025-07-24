from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.permissions import AllowAny
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
# Video views are now imported through apps.videos.urls
from apps.authentication.views import GoogleLoginView

# 전체 경로를 위한 URL 패턴들 - 모든 API는 /api/v1으로 시작
api_urls = [
    # OAuth 관련
    path('oauth/google', GoogleLoginView.as_view(), name='oauth_google'),
    
    # Avatars 관련
    path('avatars', include('apps.avatars.urls')),
    
    # Videos 관련  
    path('videos', include('apps.videos.urls')),
    
    # Places 관련
    path('api/v1/places/', include('apps.place.urls')),
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
    patterns=[  # 실제 API만 포함 - 모든 API는 /api/v1으로 시작
        # OAuth
        path('api/v1/oauth/google/', GoogleLoginView.as_view()),
        
        # Avatars  
        path('api/v1/avatars/', include('apps.avatars.urls')),
        
        # Videos
        path('api/v1/videos/', include('apps.videos.urls')),
        
        # Places
        path('api/v1/places/', include('apps.place.urls')),
    ],
)

urlpatterns = [
    path('admin/', admin.site.urls),
] + api_urls + [
    # Swagger API 문서
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # 기존 api/auth/ 경로는 제거됨 - 모든 인증은 /api/v1/oauth/로 통합
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 개발 환경에서 정적 파일 서빙
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
