from django.urls import path
from .views import GoogleLoginView

urlpatterns = [
    path('users/google/', GoogleLoginView.as_view()),
]