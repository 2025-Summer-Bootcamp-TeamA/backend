from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.video_viewset import VideoViewSet

# ViewSet을 위한 라우터 설정
router = DefaultRouter(trailing_slash=False)
router.register(r'videos', VideoViewSet, basename='video')

urlpatterns = [
    path('', include(router.urls)),
]