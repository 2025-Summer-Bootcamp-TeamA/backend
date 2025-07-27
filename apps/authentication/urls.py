from django.urls import path
from .views import GoogleLoginView, TestAuthView

urlpatterns = [
    path('oauth/google', GoogleLoginView.as_view(), name='google-login'),
    path('test-auth', TestAuthView.as_view(), name='test-auth'),
]