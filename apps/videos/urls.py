from django.urls import path
from . import views

urlpatterns = [
    # 영상 자동 저장 엔드포인트만 유지
    path('api/v1/videos', views.VideoUploadView.as_view(), name='video-upload'),
]