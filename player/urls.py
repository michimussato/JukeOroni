from django.urls import path
from . import views
from player.views import PlayerView


urlpatterns = [
    path('', PlayerView.as_view(), name='player_index'),
    path('play/', PlayerView.play, name='player_play'),
    path('next/', PlayerView.next, name='player_next'),
    path('stop/', PlayerView.stop, name='player_stop'),
    path('albums/', PlayerView.albums, name='player_albums'),
    path('radio/', views.radio_index, name='radio_index'),
    path('radio/stop/<int:pid>/', views.radio_stop, name='radio_stop'),
    path('radio/<str:display_name_short>/play/', views.radio_play, name='radio_play')
]
