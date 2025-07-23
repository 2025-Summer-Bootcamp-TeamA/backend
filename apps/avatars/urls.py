from django.urls import path
from .views import generate_avatar

urlpatterns = [
    path('', generate_avatar, name='generate_avatar')
]