from django.urls import path
from . import views

urlpatterns = [
    path('api/v1/posts', views.PostListView.as_view(), name='post-list'),
]