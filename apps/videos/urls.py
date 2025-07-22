# apps/videos/urls.py
from .views import UserVideoListView, VideoDeleteView, VideoDetailView

urlpatterns = [
    path('', UserVideoListView.as_view(), name='user-video-list'),
    path('<int:video_id>', VideoDetailView.as_view(), name='video-detail'),
]