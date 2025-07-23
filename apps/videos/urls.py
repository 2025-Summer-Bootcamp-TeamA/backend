from django.urls import path
from .views.video_creation_view import VideoCreationView
from .views.video_crud_views import VideoUploadView

urlpatterns = [
    path('generate', VideoCreationView.as_view(), name='video_generation'),
    path('', VideoUploadView.as_view(), name='video-upload'),
]