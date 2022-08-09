import logging
import time

from django.contrib import admin
from django_object_actions import DjangoObjectActions
from jukeoroni.settings import Settings
from .views import jukeoroni


# Register your models here.
from .models import Artist, Album, Track, Channel, Station, Podcast, Episode, Video


LOG = logging.getLogger(__name__)
LOG.setLevel(Settings.DJANGO_LOGGING_LEVEL)


"""
https://pythonprogramming.net/working-foreign-keys-django-tutorial/?completed=/foreign-keys-django-tutorial/

class TutorialAdmin(admin.ModelAdmin):

    fieldsets = [
        ("Title/date", {'fields': ["tutorial_title", "tutorial_published"]}),
        ("URL", {'fields': ["tutorial_slug"]}),
        ("Series", {'fields': ["tutorial_series"]}),
        ("Content", {"fields": ["tutorial_content"]})
    ]

    formfield_overrides = {
        models.TextField: {'widget': TinyMCE(attrs={'cols': 80, 'rows': 30})},
        }


admin.site.register(TutorialSeries)
admin.site.register(TutorialCategory)
admin.site.register(Tutorial,TutorialAdmin)
"""


class AlbumAdmin(admin.ModelAdmin):
    list_display = ('album_title', 'artist_name', 'year', 'album_type')
    search_fields = ['album_title', 'artist__name']
    ordering = ('artist__name', 'year', 'album_title')

    def artist_name(self, obj):
        return None if obj.artist is None else obj.artist.name

    artist_name.short_description = 'Artist'


class StationAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'channel_count')
    search_fields = ['display_name']

    def channel_count(self, obj):
        channels = Channel.objects.filter(station_id=obj.id)
        return len(channels)

    channel_count.short_description = 'Channels'


class ChannelAdmin(admin.ModelAdmin):
    fieldsets = [('Name', {'fields': ['display_name', 'display_name_short', 'station']}),
                 ('URL\'s', {'fields': ['url', 'url_logo']}),
                 ('Options', {'fields': ['is_enabled', 'show_rds']}),
                 ('Auto Playback', {'fields': ['last_played']})]
    list_display = ('display_name', 'station_display_name', 'station_image', 'show_rds', 'is_enabled')
    search_fields = ['display_name', 'station__display_name']
    # autocomplete_fields = ['display_name']

    def station_display_name(self, obj):
        return None if obj.station is None else obj.station.display_name

    def station_image(self, obj):
        return bool(obj.url_logo)
    station_image.boolean = True

    station_display_name.short_description = 'Station'


class AristAdmin(admin.ModelAdmin):
    list_display = ('name', 'album_count', 'track_count')
    search_fields = ['name']
    ordering = ('name',)

    def album_count(self, obj):
        albums = Album.objects.filter(artist_id=obj.id)
        return len(albums)

    album_count.short_description = 'Albums'

    def track_count(self, obj):
        tracks = Track.objects.filter(album__artist_id=obj.id)
        return len(tracks)

    track_count.short_description = 'Tracks'


class TrackAdmin(admin.ModelAdmin):
    list_display = ('artist_name', 'album_year', 'album_album_title', 'track_title')
    search_fields = ['track_title', 'album__album_title', 'album__artist__name']
    ordering = ('album__artist__name', 'album__year', 'album__album_title')

    def album_year(self, obj):
        return None if obj.album is None else obj.album.year

    album_year.short_description = 'Year'

    def album_album_title(self, obj):
        return None if obj.album is None else obj.album.album_title

    album_album_title.short_description = 'Album'

    def artist_name(self, obj):
        if obj.album is None:
            return None
        return None if obj.album.artist is None else obj.album.artist.name

    artist_name.short_description = 'Artist'


class VideoAdmin(DjangoObjectActions, admin.ModelAdmin):
    video = None
    # global jukeoroni

    def play_pause(self, request, obj):
        if isinstance(self.video, Video) and self.video != obj:
            LOG.warning(f'Looks like a different video {self.video.video_title} is still playing...')
            self.stop(request, obj)
            # self.video = None

        if self.video is None:
            if jukeoroni.mode != Settings.MODES['jukeoroni']['standby']:
                LOG.warning('Get JukeOroni into Standby mode before playing a video.')
                return
                # modifiy the jukeoroni mode directly
            jukeoroni.mode = Settings.MODES['videobox']['on_air']['random']
            LOG.warning(f'Starting playback of {obj.video_title} now...')
            self.video = obj
            # self.video.play(jukeoroni)
            self.video.play()
            while self.video.omxplayer is None:
                time.sleep(0.1)
            self.video.omxplayer.stopEvent += lambda _player: self.event_stop()
            self.video.omxplayer.exitEvent += lambda _player, _exit_status: self.event_exit()
        else:
            self.video.play()
            # LOG.warning(f'{obj.video_title} is currently playing.')
            # obj.play()
            # LOG.warning(f'{obj.video_title} is currently playing.')

        LOG.warning('done')
        # else:
        #     self.video.play_pause()

    def _stop(self):
        self.video.stop()
        self.video = None

    def stop(self, request, obj):

        if self.video is not None:
            LOG.warning(f'Trying to stop {self.video.video_title}...')
            LOG.warning(f'Stopping {self.video.video_title}...')
            obj.stop()
            try:
                # This is not working in case we want
                # we play matrix, go to guardians and play it,
                # and go back to matrix to play it again

                # play/pause matrix
                # go to guardians
                # play/pause guardians
                # go to matrix
                # play/pause matrix
                # error

                # maybe too fast? sleep?

                # it does work in case we start a movie and stop it
                # properly
                """
May 25 12:00:13 jukeoroni gunicorn[7649]: [05-25-2022 12:00:13] [WARNING ] [MainThread|3069315792], File "/data/django/jukeoroni/player/admin.py", line 126, in play_pause:    Starting playback of The Matrix now...
May 25 12:00:13 jukeoroni gunicorn[7649]: [05-25-2022 12:00:13] [WARNING ] [MainThread|3069315792], File "/data/django/jukeoroni/player/admin.py", line 132, in play_pause:    done
May 25 12:00:14 jukeoroni kernel: [78628.611462] pcm512x 1-004c: No SCLK, using BCLK: -2



May 25 12:00:31 jukeoroni gunicorn[7649]: [05-25-2022 12:00:31] [WARNING ] [MainThread|3069315792], File "/data/django/jukeoroni/player/admin.py", line 121, in play_pause:    Looks like a different video The Matrix is still playing...
May 25 12:00:31 jukeoroni gunicorn[7649]: [05-25-2022 12:00:31] [WARNING ] [MainThread|3069315792], File "/data/django/jukeoroni/player/admin.py", line 141, in stop:    Trying to stop The Matrix...
May 25 12:00:31 jukeoroni gunicorn[7649]: [05-25-2022 12:00:31] [WARNING ] [MainThread|3069315792], File "/data/django/jukeoroni/player/admin.py", line 143, in stop:    Stopping The Matrix...
May 25 12:00:31 jukeoroni gunicorn[7649]: [05-25-2022 12:00:31] [WARNING ] [MainThread|3069315792], File "/data/django/jukeoroni/player/admin.py", line 155, in stop:    The Matrix stopped.
May 25 12:00:31 jukeoroni gunicorn[7649]: [05-25-2022 12:00:31] [WARNING ] [MainThread|3069315792], File "/data/django/jukeoroni/player/admin.py", line 126, in play_pause:    Starting playback of Guardians of the Galaxy now...
May 25 12:00:31 jukeoroni gunicorn[7649]: [05-25-2022 12:00:31] [WARNING ] [MainThread|3069315792], File "/data/django/jukeoroni/player/admin.py", line 132, in play_pause:    done
May 25 12:00:31 jukeoroni kernel: [78646.281915] pcm512x 1-004c: No SCLK, using BCLK: -2



May 25 12:00:44 jukeoroni gunicorn[7649]: [05-25-2022 12:00:44] [WARNING ] [MainThread|3069315792], File "/data/django/jukeoroni/player/admin.py", line 121, in play_pause:    Looks like a different video Guardians of the Galaxy is still playing...
May 25 12:00:44 jukeoroni gunicorn[7649]: [05-25-2022 12:00:44] [WARNING ] [MainThread|3069315792], File "/data/django/jukeoroni/player/admin.py", line 141, in stop:    Trying to stop Guardians of the Galaxy...
May 25 12:00:44 jukeoroni gunicorn[7649]: [05-25-2022 12:00:44] [WARNING ] [MainThread|3069315792], File "/data/django/jukeoroni/player/admin.py", line 143, in stop:    Stopping Guardians of the Galaxy...
May 25 12:00:44 jukeoroni gunicorn[7649]: [05-25-2022 12:00:44] [ERROR   ] [MainThread|3069315792], File "/data/django/jukeoroni/player/admin.py", line 153, in stop:    Bullshit Error
May 25 12:00:44 jukeoroni gunicorn[7649]: Traceback (most recent call last):
May 25 12:00:44 jukeoroni gunicorn[7649]:   File "/data/django/jukeoroni/player/admin.py", line 151, in stop
May 25 12:00:44 jukeoroni gunicorn[7649]:     self.video.stop()
May 25 12:00:44 jukeoroni gunicorn[7649]:   File "/data/django/jukeoroni/player/models.py", line 201, in stop
May 25 12:00:44 jukeoroni gunicorn[7649]:     if self.omxplayer.is_playing():
May 25 12:00:44 jukeoroni gunicorn[7649]:   File "/data/venv/lib/python3.7/site-packages/decorator.py", line 232, in fun
May 25 12:00:44 jukeoroni gunicorn[7649]:     return caller(func, *(extras + args), **kw)
May 25 12:00:44 jukeoroni gunicorn[7649]:   File "/data/venv/lib/python3.7/site-packages/omxplayer/player.py", line 48, in wrapped
May 25 12:00:44 jukeoroni gunicorn[7649]:     return fn(self, *args, **kwargs)
May 25 12:00:44 jukeoroni gunicorn[7649]:   File "/data/venv/lib/python3.7/site-packages/decorator.py", line 232, in fun
May 25 12:00:44 jukeoroni gunicorn[7649]:     return caller(func, *(extras + args), **kw)
May 25 12:00:44 jukeoroni gunicorn[7649]:   File "/data/venv/lib/python3.7/site-packages/omxplayer/player.py", line 85, in wrapped
May 25 12:00:44 jukeoroni gunicorn[7649]:     return from_dbus_type(fn(self, *args, **kwargs))
May 25 12:00:44 jukeoroni gunicorn[7649]:   File "/data/venv/lib/python3.7/site-packages/omxplayer/player.py", line 783, in is_playing
May 25 12:00:44 jukeoroni gunicorn[7649]:     self._is_playing = (self.playback_status() == "Playing")
May 25 12:00:44 jukeoroni gunicorn[7649]:   File "/data/venv/lib/python3.7/site-packages/decorator.py", line 232, in fun
May 25 12:00:44 jukeoroni gunicorn[7649]:     return caller(func, *(extras + args), **kw)
May 25 12:00:44 jukeoroni gunicorn[7649]:   File "/data/venv/lib/python3.7/site-packages/omxplayer/player.py", line 48, in wrapped
May 25 12:00:44 jukeoroni gunicorn[7649]:     return fn(self, *args, **kwargs)
May 25 12:00:44 jukeoroni gunicorn[7649]:   File "/data/venv/lib/python3.7/site-packages/decorator.py", line 232, in fun
May 25 12:00:44 jukeoroni gunicorn[7649]:     return caller(func, *(extras + args), **kw)
May 25 12:00:44 jukeoroni gunicorn[7649]:   File "/data/venv/lib/python3.7/site-packages/omxplayer/player.py", line 85, in wrapped
May 25 12:00:44 jukeoroni gunicorn[7649]:     return from_dbus_type(fn(self, *args, **kwargs))
May 25 12:00:44 jukeoroni gunicorn[7649]:   File "/data/venv/lib/python3.7/site-packages/omxplayer/player.py", line 387, in playback_status
May 25 12:00:44 jukeoroni gunicorn[7649]:     return self._player_interface_property('PlaybackStatus')
May 25 12:00:44 jukeoroni gunicorn[7649]:   File "/data/venv/lib/python3.7/site-packages/omxplayer/player.py", line 860, in _player_interface_property
May 25 12:00:44 jukeoroni gunicorn[7649]:     return self._interface_property(self._player_interface.dbus_interface, prop, val)
May 25 12:00:44 jukeoroni gunicorn[7649]:   File "/data/venv/lib/python3.7/site-packages/omxplayer/player.py", line 854, in _interface_property
May 25 12:00:44 jukeoroni gunicorn[7649]:     return self._properties_interface.Get(interface, prop)
May 25 12:00:44 jukeoroni gunicorn[7649]:   File "/data/venv/lib/python3.7/site-packages/dbus/proxies.py", line 147, in __call__
May 25 12:00:44 jukeoroni gunicorn[7649]:     **keywords)
May 25 12:00:44 jukeoroni gunicorn[7649]:   File "/data/venv/lib/python3.7/site-packages/dbus/connection.py", line 653, in call_blocking
May 25 12:00:44 jukeoroni gunicorn[7649]:     message, timeout)
May 25 12:00:44 jukeoroni gunicorn[7649]: dbus.exceptions.DBusException: org.freedesktop.DBus.Error.ServiceUnknown: The name :1.2 was not provided by any .service files
May 25 12:00:44 jukeoroni gunicorn[7649]: [05-25-2022 12:00:44] [WARNING ] [MainThread|3069315792], File "/data/django/jukeoroni/player/admin.py", line 155, in stop:    Guardians of the Galaxy stopped.
May 25 12:00:44 jukeoroni gunicorn[7649]: [05-25-2022 12:00:44] [WARNING ] [MainThread|3069315792], File "/data/django/jukeoroni/player/admin.py", line 126, in play_pause:    Starting playback of The Matrix now...
May 25 12:00:44 jukeoroni gunicorn[7649]: [05-25-2022 12:00:44] [WARNING ] [MainThread|3069315792], File "/data/django/jukeoroni/player/admin.py", line 132, in play_pause:    done
                """
                # _video_title = self.video.video_title
                self.video.stop()
            except Exception:
                LOG.exception('Bullshit Error')
                _video_title = 'Bullshit Error Here!!!!'
            finally:
                LOG.warning(f'{self.video.video_title} stopped.')
                # self.reset_mode()
                # jukeoroni.mode = Settings.MODES['jukeoroni']['standby']  # [jukeoroni.jukebox.loader_mode]
            # LOG.warning(f'{obj.video_title} stopped.')
            # LOG.warning(f'{self.video.video_title} stopped.')
            # self.video = None
        else:
            LOG.warning('Nothing is currently playing.')

    def event_stop(self):
        LOG.info(f'eventStop: {self.video.video_title} stopped.')
        # eventStop() quits the player, hence: it calls eventExit()
        # afterwards. No reset_mode needed here
        # self.reset_mode()

    def event_exit(self):
        LOG.info(f'eventExit: {self.video.video_title} finished.')
        self.reset_mode()

    def reset_mode(self):
        self.video = None
        LOG.info('Resetting JukeOroni mode to jukeoroni standby')
        jukeoroni.mode = Settings.MODES['jukeoroni']['standby']  # [jukeoroni.jukebox.loader_mode]

    play_pause.label = 'Play/Pause'
    # play_pause.short_description = 'Desc'

    stop.label = 'Stop'

    list_display = ('video_title', 'video_source')
    search_fields = ['video_title', 'video_source']
    change_actions = ('play_pause', 'stop')


admin.site.register(Artist, AristAdmin)
admin.site.register(Album, AlbumAdmin)
admin.site.register(Track, TrackAdmin)
admin.site.register(Station, StationAdmin)
admin.site.register(Channel, ChannelAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(Podcast)
admin.site.register(Episode)
