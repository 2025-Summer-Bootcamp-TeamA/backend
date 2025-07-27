from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework.permissions import AllowAny
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.authentication import JWTAuthentication
# Video views are now imported through apps.videos.urls

# 루트 경로 처리 - API 서버 상태 확인
def root_api_view(request):
    return JsonResponse({
        'message': 'TeamA API Server is running! 🚀',
        'status': 'healthy',
        'version': 'v1',
        'endpoints': {
            'api_docs': '/swagger/',
            'admin': '/admin/',
            'api_base': '/api/v1/'
        }
    })

# 전체 경로를 위한 URL 패턴들 - 모든 API는 /api/v1으로 시작하고 도메인별로 분류됨
api_urls = [
    # Authentication 관련
    path('api/v1/', include('apps.authentication.urls')),
    
    # Avatars 관련
    path('api/v1/avatars', include('apps.avatars.urls')),
    
    # Videos 관련  
    path('api/v1/', include('apps.videos.urls')),
    
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
    authentication_classes=[JWTAuthentication],
    url='https://hiedu.site/',

    patterns=[  # 실제 API만 포함 - /api/v1 prefix + 도메인별 태그 분류
        # Authentication
        path('api/v1/', include('apps.authentication.urls')),
        
        # Avatars  
        path('api/v1/avatars', include('apps.avatars.urls')),
        
        # Videos
        path('api/v1/', include('apps.videos.urls')),
        
        # Places
        path('api/v1/places/', include('apps.place.urls')),
    ],
)

# 스웨거 보안 정의 추가
schema_view.security_definitions = {
    'Bearer': {
        'type': 'apiKey',
        'name': 'Authorization',
        'in': 'header'
    }
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', root_api_view, name='api-root'),  # 루트 경로 - API 상태 확인
] + api_urls + [
    # Swagger API 문서
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    # 모든 API가 /api/v1/ prefix로 통합됨 - Swagger는 도메인별 태그로 분류
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 개발 환경에서 정적 파일 서빙
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
