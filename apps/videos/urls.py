from django.urls import path
from .views.video_creation_view import VideoCreationView
from .views.video_crud_views import (
    VideoDetailView, VideoDeleteView
)

urlpatterns = [
    path('videos', VideoCreationView.as_view(), name='video_generation'),
    path('videos/<int:video_id>', VideoDetailView.as_view(), name='video-detail'),
    path('videos/<int:video_id>/delete', VideoDeleteView.as_view(), name='video-delete'),
]