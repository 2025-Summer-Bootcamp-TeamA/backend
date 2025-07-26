from django.urls import path
from .views.video_creation_view import VideoCreationView
from .views.video_crud_views import VideoUploadView
from .views.visionstory_latest_view import VisionStoryLatestVideoView, VisionStoryVideoStatusView

urlpatterns = [
    path('videos/generate', VideoCreationView.as_view(), name='video_generation'),
    path('videos/visionstory', VisionStoryLatestVideoView.as_view(), name='visionstory_latest'),
    path('videos/visionstory/status', VisionStoryVideoStatusView.as_view(), name='visionstory_status'),
    path('videos', VideoUploadView.as_view(), name='video-upload'),
]