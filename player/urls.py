from django.urls import path
from player.views import PlayerView

urlpatterns = [
    path('', PlayerView.as_view(), name='player_index'),
    path('play_next/', PlayerView.play_next, name='player_play_next'),
    path('stop/', PlayerView.stop, name='player_stop'),
    path('switch_mode/', PlayerView.switch_mode, name='player_switch_mode'),
    path('albums/<int:album_id>', PlayerView.play_album, name='player_play_album'),
    path('albums/', PlayerView.albums, name='player_albums'),
]

