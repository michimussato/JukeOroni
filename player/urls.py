from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='player_index'),
    path('radio/', views.radio_index, name='radio_index'),
    path('radio/stop/<int:pid>/', views.radio_stop, name='radio_stop'),
    path('radio/<str:display_name_short>/play/', views.radio_play, name='radio_play')
]
