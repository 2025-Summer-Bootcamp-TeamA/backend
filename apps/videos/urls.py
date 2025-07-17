from django.urls import path
from .views import VideoUploadView

urlpatterns = [
    # 영상 저장 엔드포인트
    path('', VideoUploadView.as_view(), name='video-upload'),
    
    # TODO: 추후 추가할 엔드포인트들
    # path('list/', VideoListView.as_view(), name='video-list'),
    # path('<int:pk>/', VideoDetailView.as_view(), name='video-detail'),
    # path('<int:pk>/update/', VideoUpdateView.as_view(), name='video-update'),
    # path('<int:pk>/delete/', VideoDeleteView.as_view(), name='video-delete'),
    # path('create/', VideoCreationView.as_view(), name='video-create'),  # 작품 기반 영상 생성
]