from django.urls import path
from player.views import JukeOroniView

urlpatterns = [
    path('', JukeOroniView.as_view(), name='jukeoroni_index'),
    path('play_next/', JukeOroniView.play_next, name='player_play_next'),
    path('stop/', JukeOroniView.stop, name='player_stop'),
    path('switch_mode/', JukeOroniView.switch_mode, name='player_switch_mode'),
    path('albums/<int:album_id>', JukeOroniView.play_album, name='player_play_album'),
    path('albums/', JukeOroniView.albums, name='player_albums'),
]

