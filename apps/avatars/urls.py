from django.urls import path
from .views import generate_avatar, AvatarListView

urlpatterns = [
    path('', AvatarListView.as_view(), name='avatar-list'),  # GET: 아바타 목록 조회
    path('generate/', generate_avatar, name='generate_avatar'),  # POST: 아바타 생성
]