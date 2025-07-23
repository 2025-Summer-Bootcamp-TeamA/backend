from django.urls import path
from .views import NearbyMuseumView

urlpatterns = [
    path("museums/", NearbyMuseumView.as_view(), name="places_museums_search"),
]
