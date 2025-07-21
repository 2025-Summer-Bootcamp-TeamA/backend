# apps/videos/urls.py
from django.urls import path
from .views import UserVideoListView, VideoDeleteView

urlpatterns = [
    path('', UserVideoListView.as_view(), name='user-video-list'),
    path('<int:video_id>', VideoDeleteView.as_view(), name='video-delete'),
]