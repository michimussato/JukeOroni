import os
import time
import shutil
import tempfile
import threading
import multiprocessing
import subprocess
import logging
from PIL import Image
from pydub.utils import mediainfo
from player.jukeoroni.images import Resource
from player.models import Track as DjangoTrack


from player.jukeoroni.settings import Settings


LOG = logging.getLogger(__name__)
LOG.setLevel(Settings.GLOBAL_LOGGING_LEVEL)


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
        self.cache_tmp = None
        self._cache_task_thread = None
        self._cache_online_covers_task_thread = None

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
                    LOG.info(f'removed from local filesystem: \"{self.cache_tmp}\"')
                except (OSError, TypeError):
                    LOG.exception('Cached track could not be deleted:')

    def play(self, jukeoroni):
        try:
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
