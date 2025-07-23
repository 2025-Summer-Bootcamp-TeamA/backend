from django.urls import path
from .views import AvatarListView

urlpatterns = [
    path('', AvatarListView.as_view(), name='avatars'),  # GET: 아바타 목록 조회, POST: 아바타 생성
]