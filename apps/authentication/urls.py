from django.urls import path
from .views import GoogleLoginView

urlpatterns = [
    path('oauth/google', GoogleLoginView.as_view(), name='google-login'),
]