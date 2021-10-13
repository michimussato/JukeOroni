from django.urls import path
from player.views import JukeOroniView

urlpatterns = [
    path('', JukeOroniView.as_view(), name='jukeoroni_index'),
    # Jukebox
    path('jukebox/', JukeOroniView.jukebox_index, name='jukebox'),
    path('jukebox/<int:queue_index>/pop/', JukeOroniView.pop_track_from_queue, name='jukebox pop track'),
    path('jukebox/<int:queue_index>/as_first/', JukeOroniView.set_first_in_queue, name='jukebox pop track'),
    path('set_jukebox/', JukeOroniView.set_jukebox, name='set mode jukebox'),
    path('set_radio/', JukeOroniView.set_radio, name='set mode radio'),
    path('set_standby/', JukeOroniView.set_standby, name='set mode standby'),
    path('jukebox/play_next/', JukeOroniView.play_next, name='player_play_next'),
    path('jukebox/stop/', JukeOroniView.stop, name='player_stop'),
    path('jukebox/switch_mode/', JukeOroniView.switch_mode, name='player_switch_mode'),

    # path('jukebox/albums/<int:album_id>', JukeOroniView.play_album, name='player_play_album'),
    # path('jukebox/albums/', JukeOroniView.albums, name='player_albums'),
    # Radio
    path('radio/', JukeOroniView.radio_index, name='radio'),
    path('radio/<str:display_name_short>/play/', JukeOroniView.radio_play, name='radio_play'),
    path('radio/stop/', JukeOroniView.radio_stop, name='radio_stop'),
]

