import time

from django.db import models
from pathlib import Path
import threading
import logging
from omxplayer.player import OMXPlayer

from player.models_mixins import JukeOroniMediumAbstract
from jukeoroni.settings import Settings
# from jukeoroni.settings
# from player.jukeoroni.settings import LOG


LOG = logging.getLogger(__name__)
LOG.setLevel(Settings.GLOBAL_LOGGING_LEVEL)


# # Create singleton OMXPlayer
# class JukeOroniOMX(OMXPlayer):
#     _instance = None
#
#     def __new__(cls, *args, **kwargs):
#         if cls._instance is None:
#             cls._instance = super(JukeOroniOMX, cls).__new__(cls, *args, **kwargs)
#             return cls._instance
#         else:
#             raise Exception('A OMXPlayer instance already exists.')


# # Abstract classes here
# class JukeOroniMediumAbstract(models.Model):
#
#     class Meta:
#         abstract = True
#
#     def play(self):
#         raise NotImplementedError()
#
#     def stop(self):
#         raise NotImplementedError()
#
#     @property
#     def source_file(self):
#         raise NotImplementedError()


# Create your models here.
class Artist(models.Model):
    name = models.CharField(max_length=200, unique=True, blank=False, null=False)
    cover_online = models.CharField(max_length=200, unique=False, blank=True, null=True)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class Album(models.Model):
    artist = models.ForeignKey(Artist, on_delete=models.PROTECT)
    album_title = models.CharField(max_length=200, unique=False, blank=False)
    album_type = models.CharField(max_length=200, unique=False, blank=False, null=True, default=None)
    year = models.CharField(max_length=200, unique=False, blank=True, null=False)
    cover = models.CharField(max_length=200, unique=False, blank=True, null=True)

    cover_online = models.CharField(max_length=200, unique=False, blank=True, null=True)
    # disable_artist_cover = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.album_title}'

    def __repr__(self):
        return f'{self.album_title}'


class Track(models.Model):
    track_title = models.CharField(max_length=200, unique=False, blank=True, null=True)
    album = models.ForeignKey(Album, on_delete=models.PROTECT, null=True)
    audio_source = models.CharField(max_length=200, unique=True, blank=False, null=False)
    played = models.IntegerField(default=0, unique=False)

    def __str__(self):
        return self.audio_source

    def __repr__(self):
        return self.audio_source


class Station(models.Model):
    display_name = models.CharField(max_length=200, unique=True, null=False, blank=False)
    display_name_short = models.CharField(max_length=200, unique=True, null=False, blank=False)

    def __str__(self):
        return self.display_name_short


class Channel(models.Model):
    station = models.ForeignKey(Station, on_delete=models.PROTECT, null=True, blank=True)
    # station_display_name = None if station is None else station.display_name
    display_name = models.CharField(max_length=200, unique=True, null=False, blank=False)
    display_name_short = models.CharField(max_length=200, unique=True, null=False, blank=False)
    url = models.URLField(max_length=200, unique=True, null=False, blank=False)
    url_logo = models.URLField(max_length=200, unique=False, null=True, blank=True)
    is_enabled = models.BooleanField(default=True)
    last_played = models.BooleanField(default=False)
    show_rds = models.BooleanField(default=True)

    # @property
    # def station_display_name(self):
    #     return None if self.station is None else self.station.display_name

    def __str__(self):
        return self.display_name_short

    def __repr__(self):
        return self.display_name_short


class Podcast(models.Model):
    title_channel = models.CharField(max_length=200, editable=True, unique=False, null=False, blank=False)
    image_url = models.URLField(max_length=200, editable=True, unique=False, null=False, blank=False)
    author_channel = models.CharField(max_length=200, editable=True, unique=False, null=False, blank=False)
    # channel = models.CharField(max_length=200, unique=True, null=False, blank=False)
    # station = models.ForeignKey(Station, on_delete=models.PROTECT, null=True, blank=True)
    # display_name = models.CharField(max_length=200, editable=True, unique=False, null=False, blank=False)
    # display_name_short = models.CharField(max_length=200, editable=False, unique=False, null=False, blank=False)
    url = models.URLField(max_length=200, editable=True, unique=True, null=False, blank=False)
    is_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.author_channel} - {self.title_channel}'

    def __repr__(self):
        return f'{self.author_channel} - {self.title_channel}'


class Episode(models.Model):
    podcast = models.ForeignKey(Podcast, on_delete=models.CASCADE, null=False, blank=False)
    title_episode = models.CharField(default=None, max_length=200, unique=False, null=True, blank=True)
    author_episode = models.CharField(default=None, max_length=200, unique=False, null=True, blank=True)
    duration = models.CharField(default=None, max_length=200, unique=False, null=True, blank=True)
    pub_date = models.DateTimeField(default=None, blank=True, unique=False, null=True)
    # attrib =
    # guid = models.UUIDField(default=None, editable=False, blank=False, null=True)
    guid = models.CharField(max_length=200, default=None, unique=True, editable=True, blank=False, null=True)
    meta_type = models.CharField(default=None, max_length=200, unique=False, null=True, blank=True)
    length = models.CharField(default=None, max_length=200, unique=False, null=True, blank=True)
    url = models.URLField(default=None, unique=True, null=False, blank=False)
    # played = models.BooleanField(default=False)
    progress = models.FloatField(default=0.0, null=False, blank=False)
    # time_mark =

    def __str__(self):
        return f'{self.podcast.title_channel} - {self.title_episode}'

    def __repr__(self):
        return f'{self.podcast.title_channel} - {self.title_episode}'


# class Setting(models.Model):
#     key = models.CharField()
#     data_type = models.CharField()
#     values = models.
#     index = models.Index


class Video(models.Model):
    video_source = models.CharField(max_length=200, unique=True, blank=False, null=False)
    video_title = models.CharField(max_length=200, unique=True, blank=False, null=False)
    is_playing = models.BooleanField(default=False)

    """
    Custom methods and attributes
    Could be solved with inheritance too, but this
    seems more elegant
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.omxplayer = None
        self._start_paused = False

    # def play(self, jukeoroni=None):
    def play(self):
        # self._omxplayer_thread = threading.Thread(target=self._play, kwargs={'jukeoroni': jukeoroni})
        self._omxplayer_thread = threading.Thread(target=self._play)
        self._omxplayer_thread.name = f'OMXPlayer Playback Thread ({self.video_title})'
        self._omxplayer_thread.daemon = False
        self._omxplayer_thread.start()

    # def _play(self, **kwargs):
    def _play(self):
        self.omxplayer = OMXPlayer(
            self.source_file.as_posix(),
            args=['--no-keys', '--adev', Settings.AUDIO_OUT],
            # dbus_name='org.mpris.MediaPlayer2.omxplayer1',
            pause=self._start_paused,
        )

    def stop(self):
        """Stop the playback; will quit the Player"""
        if isinstance(self.omxplayer, OMXPlayer):
            if self.omxplayer.is_playing():
                self.omxplayer.stop()
                self.omxplayer = None

    def play_pause(self):
        if isinstance(self.omxplayer, OMXPlayer):
            self.omxplayer.play_pause()

    @property
    def source_file(self):
        return Path(Settings.VIDEO_DIR) / self.video_source
