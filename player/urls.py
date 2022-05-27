from django.urls import path
from player.views import JukeOroniView, BoxView, BoxViewRadio


urlpatterns = [
    # Jukebox
    path('', JukeOroniView.as_view(), name='jukeoroni_index'),
    path('jukebox/', BoxView.as_view(), name='jukebox'),
    path('radio/', BoxViewRadio.as_view(), name='radio'),
    path('meditationbox/', BoxView.as_view(), name='meditationbox'),
    path('podcastbox/', BoxView.as_view(), name='podcastbox'),
    path('videobox/', BoxView.as_view(), name='videobox'),
    # path('audiobookbox/', JukeOroniView.box_index, name='audiobookbox'),
    path('jukebox/<int:queue_index>/pop/', JukeOroniView.pop_track_from_queue, name='jukebox pop track'),
    path('meditationbox/<int:queue_index>/pop/', JukeOroniView.pop_track_from_queue, name='meditationbox pop track'),
    path('podcastbox/<int:queue_index>/pop/', JukeOroniView.pop_track_from_queue, name='podcastbox pop track'),
    # path('audiobookbox/<int:queue_index>/pop/', JukeOroniView.pop_track_from_queue, name='audiobookbox pop track'),
    path('jukebox/<int:queue_index>/as_first/', JukeOroniView.set_first_in_queue, name='jukebox set first'),
    path('meditationbox/<int:queue_index>/as_first/', JukeOroniView.set_first_in_queue, name='meditationbox set first'),
    path('podcastbox/<int:queue_index>/as_first/', JukeOroniView.set_first_in_queue, name='podcastbox set first'),
    # path('audiobookbox/<int:queue_index>/as_first/', JukeOroniView.set_first_in_queue, name='audiobookbox set first'),
    path('set_jukebox/', JukeOroniView.set_jukebox, name='set mode jukebox'),
    path('set_meditationbox/', JukeOroniView.set_meditationbox, name='set mode meditation'),
    path('set_podcastbox/', JukeOroniView.set_podcastbox, name='set mode podcast'),
    path('set_videobox/', JukeOroniView.set_videobox, name='set mode video'),
    # path('set_audiobookbox/', JukeOroniView.set_audiobookbox, name='set mode audiobookbox'),
    path('set_radio/', JukeOroniView.set_radio, name='set mode radio'),
    path('set_standby/', JukeOroniView.set_standby, name='set mode standby'),
    path('jukebox/play_next/', JukeOroniView.play_next, name='player_play_next'),
    path('meditationbox/play_next/', JukeOroniView.play_next, name='player_play_next'),
    path('podcastbox/play_next/', JukeOroniView.play_next, name='player_play_next'),
    path('videobox/play/', JukeOroniView.play, name='video_play'),
    path('videobox/<str:video_title>/load/', JukeOroniView.load_movie_by_title, name='video_play'),
    # path('videobox/pause/', JukeOroniView.pause, name='video_pause'),
    # path('videobox/resume/', JukeOroniView.resume_video, name='video_resume'),
    # path('audiobookbox/play_next/', JukeOroniView.play_next, name='player_play_next'),
    path('jukebox/update_track_list/', JukeOroniView.update_track_list, name='update_track_list'),
    path('meditationbox/update_track_list/', JukeOroniView.update_track_list, name='update_track_list'),
    path('podcastbox/update_track_list/', JukeOroniView.update_track_list, name='update_track_list'),
    # path('audiobookbox/update_track_list/', JukeOroniView.update_track_list, name='update_track_list'),

    path('jukebox/stop/', JukeOroniView.stop, name='player_stop'),
    path('meditationbox/stop/', JukeOroniView.stop, name='player_stop'),
    path('podcastbox/stop/', JukeOroniView.stop, name='player_stop'),
    path('videobox/stop/', JukeOroniView.stop, name='player_stop'),
    # path('audiobookbox/stop/', JukeOroniView.stop, name='player_stop'),
    path('pause/', JukeOroniView.pause, name='pause'),
    path('resume/', JukeOroniView.resume, name='resume'),
    path('jukebox/switch_mode/', JukeOroniView.switch_mode, name='player_switch_mode'),
    path('meditationbox/switch_mode/', JukeOroniView.switch_mode, name='player_switch_mode'),
    path('podcastbox/switch_mode/', JukeOroniView.switch_mode, name='player_switch_mode'),
    # path('audiobookbox/switch_mode/', JukeOroniView.switch_mode, name='player_switch_mode'),

    path('jukebox/albums/<int:album_id>/', JukeOroniView.play_album, name='player_play_album'),
    path('meditationbox/albums/<int:album_id>/', JukeOroniView.play_album, name='player_play_album'),
    path('podcastbox/albums/<int:album_id>/', JukeOroniView.play_album, name='player_play_album'),
    # path('audiobookbox/albums/<int:album_id>/', JukeOroniView.play_album, name='player_play_album'),
    path('jukebox/albums/', JukeOroniView.albums, name='player_albums'),
    path('meditationbox/albums/', JukeOroniView.albums, name='player_albums'),
    path('podcastbox/albums/', JukeOroniView.albums, name='player_albums'),
    # path('audiobookbox/albums/', JukeOroniView.albums, name='player_albums'),

    # path('jukebox/tracks/play_track/<int:track_id>/', JukeOroniView.play_track, name='player_play_track'),
    # path('jukebox/tracks/', JukeOroniView.tracks, name='player_tracks'),
    # path('meditationbox/tracks/', JukeOroniView.tracks, name='player_tracks'),

    # Radio
    path('radio/<str:display_name_short>/play/', BoxViewRadio.radio_play, name='radio_play'),
    path('radio/stop/', BoxViewRadio.radio_stop, name='radio_stop'),

    # path('', index_redirect, name='index_redirect'),
]

