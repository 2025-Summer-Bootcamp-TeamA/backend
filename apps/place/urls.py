from django.urls import path
from .views import NearbyMuseumView

app_name = 'place'

urlpatterns = [
    path(
        "museums/", 
        NearbyMuseumView.as_view(), 
        name="nearby_museums_search"
    ),
]
