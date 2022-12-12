from django.urls import path
from . import views

app_name = "maps"

urlpatterns = [
    path("map/", views.basic_map, name="basic_map"),
    path("map_elk/", views.basic_elk_map, name="basic_e_map"),
]
