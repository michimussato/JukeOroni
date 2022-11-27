import os
import time
import shutil
import tempfile
import threading
import multiprocessing
import subprocess
import logging
from PIL import ImageFile, Image
from pydub.utils import mediainfo
from player.jukeoroni.images import Resource
from player.models import Track as DjangoTrack
from player.jukeoroni.lyric_genius import get_lyrics

from player.jukeoroni.settings import Settings


LOG = logging.getLogger(__name__)
LOG.setLevel(Settings.GLOBAL_LOGGING_LEVEL)


ImageFile.LOAD_TRUNCATED_IMAGES = True


class JukeboxTrack(object):
    def __init__(self, django_track, cached=True):
        self.django_track = django_track
        self.path = os.path.join(Settings.MEDIA_ROOT, self.django_track.album.album_type, self.django_track.audio_source)
        LOG.info(self.path)
        self.cached = cached
        self.cache_tmp = None
        self.playing_proc = None
        self.killed = False

        self._cover_album = Resource().JUKEBOX_ON_AIR_DEFAULT_IMAGE
        self._cover_artist = None

        self._size = None
        self._cache_task_thread = None
        self._cache_online_covers_task_thread = None

        self._lyrics = None

    def __hash__(self):
        # we need this to remove duplicate tracks from track list (self.tracks)
        # https://stackoverflow.com/a/4173307/2207196
        return hash(('django_track', self.django_track, 'path', self.path))

    def __str__(self):
        return f'{self.artist} - {self.album} - {self.track_title}'

    def __repr__(self):
        return f'{self.artist} - {self.album} - {self.track_title}'

    @property
    def track_title(self):
        return self.django_track.track_title


    @property
    def lyrics(self):
        if self._lyrics is None:
            self._lyrics = get_lyrics(artist=self.artist, track=self.track_title)
        # else:
        return self._lyrics

    @property
    def id(self):
        return self.django_track.id

    @property
    def album_tracks(self):
        # list of tracks within an album, sorted by the file name
        # (indexes might not be incremental)
        return sorted(list(DjangoTrack.objects.filter(album=self.album.id)), key=lambda x: x.audio_source.lower())

    @property
    def first_album_track(self):
        return self.album_tracks[0]

    @property
    def is_first_album_track(self):
        if self.django_track == self.first_album_track:
            return True
        else:
            return False

    @property
    def next_album_track(self):
        this_index = self.album_tracks.index(self.django_track)
        next_index = this_index + 1

        try:
            return self.album_tracks[next_index]
        except IndexError:
            return None

    @property
    def album(self):
        return self.django_track.album

    @property
    def year(self):
        return self.album.year

    @property
    def artist(self):
        return self.album.artist

    def cache_online_covers(self):
        if Settings.CACHE_COVERS:
            self._cache_online_covers_task_thread = threading.Thread(target=self._cache_covers)
            self._cache_online_covers_task_thread.name = 'Track Cover Loader Thread'
            self._cache_online_covers_task_thread.daemon = False
            self._cache_online_covers_task_thread.start()

    def _cache_covers(self):
        self._cache_cover_album()
        self._cache_cover_artist()

    def _cache_cover_album(self):
        if self.album.cover is not None:
            LOG.info(f'Loading offline album cover for Track "{self}"...')
            self._cover_album = Image.open(os.path.join(Settings.MEDIA_ROOT, self.django_track.album.album_type, self.album.cover))
        else:
            LOG.info(f'Offline album cover for Track "{self}" is None...')

        if not Settings.COVER_ONLINE_PREFERENCE and self.album.cover is not None:
            LOG.info('Loading offline album cover...')
            self._cover_album = Image.open(os.path.join(Settings.MEDIA_ROOT, self.django_track.album.album_type, self.album.cover))

        elif Settings.COVER_ONLINE_PREFERENCE and self.album.cover_online is not None or self.album.cover is None:
            LOG.info(f'Loading online album cover for Track "{self}"...')
            _cover_album_online = Resource().from_url(url=self.album.cover_online)
            if _cover_album_online is not None:
                self._cover_album = _cover_album_online

        else:
            self._cover_album = Resource().DEFAULT_ALBUM_COVER

        # else:

        # if COVER_ONLINE_PREFERENCE:
        #     if self.album.cover_online is not None:
        #         LOG.info('Loading online album cover...')
        #         self._cover_album = Resource().from_url(url=self.album.cover_online)
        # else:
        #     if self.album.cover is not None:
        #         LOG.info('Loading offline album cover...')
        #         self._cover_album = Image.open(self.album.cover)
        LOG.info(f'Loading album cover for Track "{self}" done: {self._cover_album}')

    def _cache_cover_artist(self):
        self._cover_artist = None

        if self.artist.cover_online is not None:
            LOG.info(f'Loading online artist cover for artist "{self.artist}"...')
            self._cover_artist = Resource().from_url(url=self.artist.cover_online)

        LOG.info(f'Loading artist cover for artist "{self.artist}" done: {self._cover_artist}')

    @property
    def cover_album(self):
        # TODO: query Discogs image here on the fly?
        #  downside: we cannot specify the actual image
        #  on the database if path is not stored beforehand
        return Resource().squareify(self._cover_album)

    @property
    def cover_artist(self):
        # TODO: query Discogs image here on the fly?
        #  downside: we cannot specify the actual image
        #  on the database if path is not stored beforehand
        if str(self.artist).lower() in [str(i).lower for i in Settings.IGNORE_ARTIST_COVER]:
            return None
        if self._cover_artist is not None:
            return Resource().squareify(self._cover_artist)
        else:
            return None

    @property
    def media_info(self):
        return mediainfo(self.path)

    def _cache(self):
        LOG.info(f'copying to local filesystem: \"{self.path}\" as \"{self.cache_tmp}\"')
        shutil.copy(self.path, self.cache_tmp)

    def kill_caching_process(self):
        if self._cache_task_thread is not None:

            self._cache_task_thread.kill()
            self._cache_task_thread.join()

            self.killed = True

    def cache(self):
        if Settings.CACHE_TRACKS:
            self._cache_task_thread = multiprocessing.Process(target=self._cache)
            self._cache_task_thread.name = 'Track Cacher Progress Thread'
            self._cache_task_thread.daemon = False
            self.cache_tmp = tempfile.mkstemp()[1]
            self._cache_task_thread.start()

            _interval = float(5)
            _waited = None
            _size_cached = 0
            while self.is_caching:
                if _waited is None or _waited % _interval == 0:
                    _waited = 0

                    _gain = self.size_cached - _size_cached

                    _size_cached = self.size_cached

                    LOG.info(f'{str(round(self.size_cached / (1024.0 * 1024.0), 3))} MB of {str(round(self.size / (1024.0 * 1024.0), 3))} MB loaded'
                             f' ~({str(round(_gain / (1024.0 * 1024.0 * _interval), 3))} MB/s)'
                             f' ({self})')

                time.sleep(1.0)
                _waited += 1

    @property
    def is_caching(self):
        if self._cache_task_thread is None:
            return False
        else:
            return self._cache_task_thread.is_alive()

    @property
    def size(self):
        if self._size is None:
            self._size = os.path.getsize(self.path)
        return self._size

    @property
    def size_cached(self):
        if self.cache_tmp is None:
            return 0
        try:
            return os.path.getsize(self.cache_tmp)
        except FileNotFoundError:
            LOG.exception(f'Could not get size of cache ({self}): ')
            return 0

    @property
    def progress(self):
        #{{({str(round(box.loading_track.size_cached / (1024.0 * 1024.0), 1))}
        #      of {str(round(box.loading_track.size / (1024.0 * 1024.0), 1))} MB)}}
        # rel = round(box.loading_track.size_cached / box.loading_track.size, 1)
        return f'{str(round(self.size_cached / (1024.0 * 1024.0), 1))} of {str(round(self.size / (1024.0 * 1024.0), 1))} MB'

    @property
    def percent_cached(self):
        # {{({str(round(box.loading_track.size_cached / (1024.0 * 1024.0), 1))}
        #      of {str(round(box.loading_track.size / (1024.0 * 1024.0), 1))} MB)}}
        rel = round(self.size_cached / self.size * 100, 1)
        return f'{str(rel)} %'

    @property
    def playing_from(self):
        return self.cache_tmp if self.cached else self.path

    @property
    def is_playing(self):
        return bool(self.playing_proc)

    def __del__(self):
        if self.cached:

            if self.cache_tmp is not None:
                try:
                    os.remove(self.cache_tmp)
                    '''
Nov 21 10:54:28 jukeoroni gunicorn[811]: [11-21-2022 10:54:28] [ERROR   ] [Track Loader Thread|2917135456], File "/data/django/jukeoroni/player/jukeoroni/box_track.py", line 263, in __del__:    Cached track could not be deleted:
Nov 21 10:54:28 jukeoroni gunicorn[811]: Traceback (most recent call last):
Nov 21 10:54:28 jukeoroni gunicorn[811]:   File "/data/django/jukeoroni/player/jukeoroni/box_track.py", line 260, in __del__
Nov 21 10:54:28 jukeoroni gunicorn[811]:     os.remove(self.cache_tmp)
Nov 21 10:54:28 jukeoroni gunicorn[811]: FileNotFoundError: [Errno 2] No such file or directory: '/tmp/tmpx_rgtmrx'


root@jukeoroni:/tmp/systemd-private-6e23ef15fc82489f84b9537aeddc83ac-gunicorn.service-avetgQ/tmp# ls -al
total 1349520
drwxrwxrwt  4 root root      4096 Nov 21 10:58 .
drwx------  3 root root      4096 Nov 20 19:13 ..
-rw-r--r--  1 pi   pi       19769 Nov 21 10:55 geckodriver.log
drwx------  2 pi   pi        4096 Nov 21 10:51 pulse-PKdhtXMmr18n
drwxr-xr-x 14 pi   pi        4096 Nov 21 10:29 rust_mozprofileNt8AIc
-rw-r--r--  1 pi   pi    95282591 Nov 21 10:20 tmp2scrb925
-rw-r--r--  1 pi   pi   166276107 Nov 21 10:21 tmp5nnnq4n4
-rw-r--r--  1 pi   pi   284690286 Nov 21 10:58 tmpfifgf0b9
-rw-r--r--  1 pi   pi    49005418 Nov 21 10:19 tmp_soks1s_
-rw-r--r--  1 pi   pi   227433496 Nov 21 10:54 tmptmwn3mg0
-rw-r--r--  1 pi   pi   185632821 Nov 21 10:56 tmpuu8qickw
-rw-r--r--  1 pi   pi   373515396 Nov 21 10:55 tmpznph7hoq


Nov 21 11:15:27 jukeoroni gunicorn[811]: [11-21-2022 11:15:27] [INFO    ] [JukeOroni Playback Thread|2878280800], File "/data/django/jukeoroni/player/jukeoroni/box_track.py", line 276, in play:    playback finished: "/data/googledrive/media/audio/music/on_device/Dire Straits - 1985 - Brothers in Arms [FLAC][24][192]/03 Walk Of Life.flac"
Nov 21 11:15:27 jukeoroni gunicorn[811]: [11-21-2022 11:15:27] [INFO    ] [JukeOroni Playback Thread|2878280800], File "/data/django/jukeoroni/player/jukeoroni/jukeoroni.py", line 1027, in _playback_task:    playback finished
Nov 21 11:15:27 jukeoroni gunicorn[811]: [11-21-2022 11:15:27] [INFO    ] [State Watcher Thread|2959078496], File "/data/django/jukeoroni/player/jukeoroni/jukeoroni.py", line 1043, in insert:    Media inserted: Dire Straits - Brothers in Arms [FLAC][24][192] - 04 Your Latest Trick.flac (type <class 'player.jukeoroni.box_track.JukeboxTrack'>)
Nov 21 11:15:27 jukeoroni gunicorn[811]: [11-21-2022 11:15:27] [DEBUG   ] [State Watcher Thread|2959078496], File "/data/django/jukeoroni/player/jukeoroni/jukeoroni.py", line 900, in play_jukebox:    Starting new playback thread
Nov 21 11:15:27 jukeoroni gunicorn[811]: [11-21-2022 11:15:27] [INFO    ] [JukeOroni Playback Thread|2878280800], File "/data/django/jukeoroni/player/jukeoroni/jukeoroni.py", line 1017, in _playback_task:    starting playback thread: for /data/googledrive/media/audio/music/on_device/Dire Straits - 1985 - Brothers in Arms [FLAC][24][192]/04 Your Latest Trick.flac from /tmp/tmpfifgf0b9
Nov 21 11:15:27 jukeoroni gunicorn[811]: [11-21-2022 11:15:27] [INFO    ] [JukeOroni Playback Thread|2878280800], File "/data/django/jukeoroni/player/jukeoroni/box_track.py", line 268, in play:    starting playback: "/data/googledrive/media/audio/music/on_device/Dire Straits - 1985 - Brothers in Arms [FLAC][24][192]/04 Your Latest Trick.flac" from: "/tmp/tmpfifgf0b9"
Nov 21 11:15:27 jukeoroni nice[1199]: ERROR : media/audio/music/on_device/Dire Straits - 1985 - Brothers in Arms [FLAC][24][192]/cover.jpg: ReadFileHandle.Read error: low level retry 1/10: read tcp 192.168.0.16:47930->142.250.203.106:443: i/o timeout
'''
                    LOG.info(f'removed from local filesystem: \"{self.cache_tmp}\"')
                except (OSError, TypeError):
                    LOG.exception('Cached track could not be deleted:')

    def play(self, jukeoroni):
        try:
            # TODO while jukeoroni.repeat_track:
            LOG.info(f'starting playback: \"{self.path}\" from: \"{self.playing_from}\"')
            self.django_track.played += 1
            self.django_track.save()
            jukeoroni.playback_proc = subprocess.Popen(Settings.FFPLAY_CMD + [self.playing_from], shell=False)
            try:
                jukeoroni.playback_proc.communicate()
            except AttributeError:
                LOG.exception('track playback was stopped.')
            LOG.info(f'playback finished: \"{self.path}\"')
            # self.django_track.played += 1
        except Exception:
            LOG.exception(f'Playback failed: \"{self.path}\"')
        finally:
            # if self.cached:
            #     # TODO add to self.__delete__()
            #     os.remove(self.cache_tmp)
            #     LOG.info(f'removed from local filesystem: \"{self.cache_tmp}\"')
            jukeoroni.playback_proc = None
