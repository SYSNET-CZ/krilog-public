from django.urls import path
from . import views

app_name = "portal"

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path("new_word/", views.new_word, name="new_word"),
    path("new_demand/", views.new_demand, name="new_demand"),
    path("new_demand_plus/", views.new_demand_plus, name="new_demand_plus"),
    path("edit_demandID=<str:identifier>/", views.edit_demand, name="edit_demand"),
    path("deactivate_demandID=<str:identifier>/", views.deactivate_demand, name="deactivate_demand"),
    path('word_list/', views.word_list, name='word_list'),
    path('demand_list/', views.demand_list, name='demand_list'),
    path('offer_list/', views.offer_list, name='offer_list'),
    path('tweet_list/', views.tweet_list, name='tweet_list'),
    path('sbazar_list/', views.sbazar_list, name='sbazar_list'),
    path('bazos_list/', views.bazos_list, name='bazos_list'),
    path('elasticsearch/', views.elastic_synchro_view, name='elasticsearch'),
    path('offer_e_list/', views.offer_elk_list, name='offer_list_elk'),
    path('sbazar_e_list/', views.sbazar_elk_list, name='sbazar_list_elk'),
]
