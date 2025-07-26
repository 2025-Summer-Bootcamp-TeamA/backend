from django.urls import path
from .views.video_creation_view import VideoCreationView

urlpatterns = [
    path('videos', VideoCreationView.as_view(), name='video_generation'),
]