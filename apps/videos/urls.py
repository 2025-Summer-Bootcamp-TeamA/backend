from django.urls import path
from .views import UserVideoListView

urlpatterns = [
    path('', UserVideoListView.as_view(), name='user-video-list'),
]
