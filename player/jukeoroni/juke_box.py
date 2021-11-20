import glob
import multiprocessing
import os
import logging
import random
import shutil
import subprocess
import tempfile
import threading
import time

from PIL import Image
from pydub.utils import mediainfo

from player.jukeoroni.discogs import get_client, get_artist, get_album
from player.models import Track as DjangoTrack
from player.models import Artist
from player.jukeoroni.displays import Jukebox as JukeboxLayout
from player.jukeoroni.images import Resource
from player.jukeoroni.settings import (
    GLOBAL_LOGGING_LEVEL,
    MAX_CACHED_FILES,
    AUDIO_FILES,
    MUSIC_DIR,
    COVER_ONLINE_PREFERENCE,
    DEFAULT_TRACKLIST_REGEN_INTERVAL,
    FFPLAY_CMD,
)
from player.models import Album

LOG = logging.getLogger(__name__)
LOG.setLevel(GLOBAL_LOGGING_LEVEL)


class JukeboxTrack(object):
    def __init__(self, django_track, cached=True):
        self.django_track = django_track
        self.path = self.django_track.audio_source
        self.cached = cached
        self.cache_tmp = None
        self.playing_proc = None
        self.killed = False

        self._cover_album = Resource().JUKEBOX_ON_AIR_DEFAULT_IMAGE
        self._cover_artist = None

        self._size = None
        self.cache_tmp = None
        self._cache_task_thread = None

    def __str__(self):
        return f'{self.artist} - {self.album} - {self.track_title}'

    def __repr__(self):
        return f'{self.artist} - {self.album} - {self.track_title}'

    @property
    def track_title(self):
        return self.django_track.track_title

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
        self._cache_online_covers_task_thread = threading.Thread(target=self._cache_covers)
        self._cache_online_covers_task_thread.name = 'Track Cover Loader Thread'
        self._cache_online_covers_task_thread.daemon = False
        # self.cache_tmp = tempfile.mkstemp()[1]
        self._cache_online_covers_task_thread.start()

    def _cache_covers(self):
        self._cache_cover_album()
        self._cache_cover_artist()

    def _cache_cover_album(self):
        if self.album.cover is not None:
            LOG.info(f'Loading offline album cover for Track "{self}"...')
            self._cover_album = Image.open(self.album.cover)
        else:
            LOG.info(f'Offline album cover for Track "{self}" is None...')

        if COVER_ONLINE_PREFERENCE and self.album.cover_online is not None or self.album.cover is None:
            LOG.info(f'Loading online album cover for Track "{self}"...')
            _cover_album_online = Resource().from_url(url=self.album.cover_online)
            if _cover_album_online is not None:
                self._cover_album = _cover_album_online

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

            # self._cache_onli§_covers_task_thread.join()

            self.killed = True

    def cache(self):
        self._cache_task_thread = multiprocessing.Process(target=self._cache)
        self._cache_task_thread.name = 'Track Cacher Progress Thread'
        self._cache_task_thread.daemon = False
        self.cache_tmp = tempfile.mkstemp()[1]
        self._cache_task_thread.start()

        self.cache_online_covers()

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
            """
Traceback (most recent call last):
  File "/data/venv/lib/python3.7/site-packages/django/core/handlers/exception.py", line 47, in inner
    response = get_response(request)
  File "/data/venv/lib/python3.7/site-packages/django/core/handlers/base.py", line 181, in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
  File "/data/django/jukeoroni/player/views.py", line 166, in jukebox_index
    ret += '<center><div>{0}</div></center>'.format(f'{jukeoroni.jukebox.loading_track.artist} - {jukeoroni.jukebox.loading_track.album} ({jukeoroni.jukebox.loading_track.year}) - {jukeoroni.jukebox.loading_track.track_title} ({str(round(jukeoroni.jukebox.loading_track.size_cached / (1024.0 * 1024.0), 1))} of {str(round(jukeoroni.jukebox.loading_track.size / (1024.0 * 1024.0), 1))} MB)')
  File "/data/django/jukeoroni/player/jukeoroni/juke_box.py", line 199, in size
    self._size = os.path.getsize(self.path)
  File "/usr/lib/python3.7/genericpath.py", line 50, in getsize
    return os.stat(filename).st_size

Exception Type: FileNotFoundError at /jukeoroni/jukebox/
Exception Value: [Errno 2] No such file or directory: '/data/googledrive/media/audio/music/on_device/The Hu - 2019 - The Gereg [FLAC-16:44.1]/01 The Gereg.flac'
            """
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
            try:
                os.remove(self.cache_tmp)
                LOG.info(f'removed from local filesystem: \"{self.cache_tmp}\"')
            except OSError:
                LOG.exception('Cached track could not be deleted:')

    def play(self, jukeoroni):
        try:
            LOG.info(f'starting playback: \"{self.path}\" from: \"{self.playing_from}\"')
            self.django_track.played += 1
            self.django_track.save()
            jukeoroni.playback_proc = subprocess.Popen(FFPLAY_CMD + [self.playing_from], shell=False)
            try:
                jukeoroni.playback_proc.communicate()
            except AttributeError:
                LOG.exception('track playback was stopped.')
            LOG.info(f'playback finished: \"{self.path}\"')
            # self.django_track.played += 1
        except Exception:
            LOG.exception('playback failed: \"{0}\"'.format(self.path))
        finally:
            # if self.cached:
            #     # TODO add to self.__delete__()
            #     os.remove(self.cache_tmp)
            #     LOG.info(f'removed from local filesystem: \"{self.cache_tmp}\"')
            jukeoroni.playback_proc = None


class Jukebox(object):
    """
from player.jukeoroni.juke_box import Jukebox
box = Jukebox()
box.turn_on()

box.set_auto_update_tracklist_on()


box.turn_off()
    """
    def __init__(self, jukeoroni):

        self.on = False
        self.loader_mode = 'random'

        self.jukeoroni = jukeoroni

        self.layout = JukeboxLayout()
        self._loading_display = False

        self.playing_track = None
        self.is_on_air = None

        self.requested_album_id = None
        self._need_first_album_track = False
        self._auto_update_tracklist = False

        self.tracks = []
        # self.loading_process = None
        self.loading_track = None

        self._track_list_generator_thread = None
        self._track_loader_watcher_thread = None
        self._track_loader_thread = None

    def temp_cleanup(self):
        temp_dir = tempfile.gettempdir()
        LOG.info(f'cleaning up {temp_dir}...')
        for filename in glob.glob(os.path.join(temp_dir, 'tmp*')):
            os.remove(filename)
        LOG.info('cleanup done.')

    @property
    def next_track(self):
        if not bool(self.tracks):
            return None
        return self.tracks.pop(0)

    def turn_on(self, disable_track_loader=False):
        assert not self.on, 'Jukebox is already on.'

        self.temp_cleanup()

        self.on = True

        self.track_list_generator_thread()
        if not disable_track_loader:
            self.track_loader_thread()
        # self.track_loader_watcher_thread()

    def turn_off(self):
        assert self.on, 'Jukebox is already off.'
        self.on = False
        if self._track_list_generator_thread is not None:
            self._track_list_generator_thread.join()
            self._track_list_generator_thread = None

        self.temp_cleanup()

    ############################################
    # set modes
    def set_loader_mode_random(self):
        self.kill_loading_process()
        self.loader_mode = 'random'

    def play_album(self, album_id):
        self.requested_album_id = album_id
        self.loader_mode = 'album'
        self.kill_loading_process()

    def play_track(self, track_id):
        self.kill_loading_process()
        return DjangoTrack.objects.get(id=track_id)

    def set_loader_mode_album(self):
        self.kill_loading_process()
        self.loader_mode = 'album'
        self._need_first_album_track = True
    ############################################

    def set_auto_update_tracklist_on(self):
        self._auto_update_tracklist = True

    def set_auto_update_tracklist_off(self):
        self._auto_update_tracklist = False

    @property
    def playback_proc(self):
        return self.playing_track.playback_proc

    ############################################
    # track list generator
    # only start this thread if auto_update_tracklist
    # is required. otherwise simply call create_update_track_list
    # once.
    # this is not returning non picklable objects
    # so hopefully ideal for multiprocessing
    # can't use multiprocessing because the main thread is
    # altering self.on
    """
Nov  1 19:11:03 jukeoroni gunicorn[611]: Exception in thread Track List Generator Process:
Nov  1 19:11:03 jukeoroni gunicorn[611]: Traceback (most recent call last):
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/urllib3/connectionpool.py", line 706, in urlopen
Nov  1 19:11:03 jukeoroni gunicorn[611]:     chunked=chunked,
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/urllib3/connectionpool.py", line 382, in _make_request
Nov  1 19:11:03 jukeoroni gunicorn[611]:     self._validate_conn(conn)
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/urllib3/connectionpool.py", line 1010, in _validate_conn
Nov  1 19:11:03 jukeoroni gunicorn[611]:     conn.connect()
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/urllib3/connection.py", line 421, in connect
Nov  1 19:11:03 jukeoroni gunicorn[611]:     tls_in_tls=tls_in_tls,
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/urllib3/util/ssl_.py", line 450, in ssl_wrap_socket
Nov  1 19:11:03 jukeoroni gunicorn[611]:     sock, context, tls_in_tls, server_hostname=server_hostname
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/urllib3/util/ssl_.py", line 493, in _ssl_wrap_socket_impl
Nov  1 19:11:03 jukeoroni gunicorn[611]:     return ssl_context.wrap_socket(sock, server_hostname=server_hostname)
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/usr/lib/python3.7/ssl.py", line 412, in wrap_socket
Nov  1 19:11:03 jukeoroni gunicorn[611]:     session=session
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/usr/lib/python3.7/ssl.py", line 853, in _create
Nov  1 19:11:03 jukeoroni gunicorn[611]:     self.do_handshake()
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/usr/lib/python3.7/ssl.py", line 1117, in do_handshake
Nov  1 19:11:03 jukeoroni gunicorn[611]:     self._sslobj.do_handshake()
Nov  1 19:11:03 jukeoroni gunicorn[611]: ConnectionResetError: [Errno 104] Connection reset by peer
Nov  1 19:11:03 jukeoroni gunicorn[611]: During handling of the above exception, another exception occurred:
Nov  1 19:11:03 jukeoroni gunicorn[611]: Traceback (most recent call last):
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/requests/adapters.py", line 449, in send
Nov  1 19:11:03 jukeoroni gunicorn[611]:     timeout=timeout
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/urllib3/connectionpool.py", line 756, in urlopen
Nov  1 19:11:03 jukeoroni gunicorn[611]:     method, url, error=e, _pool=self, _stacktrace=sys.exc_info()[2]
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/urllib3/util/retry.py", line 532, in increment
Nov  1 19:11:03 jukeoroni gunicorn[611]:     raise six.reraise(type(error), error, _stacktrace)
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/urllib3/packages/six.py", line 769, in reraise
Nov  1 19:11:03 jukeoroni gunicorn[611]:     raise value.with_traceback(tb)
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/urllib3/connectionpool.py", line 706, in urlopen
Nov  1 19:11:03 jukeoroni gunicorn[611]:     chunked=chunked,
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/urllib3/connectionpool.py", line 382, in _make_request
Nov  1 19:11:03 jukeoroni gunicorn[611]:     self._validate_conn(conn)
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/urllib3/connectionpool.py", line 1010, in _validate_conn
Nov  1 19:11:03 jukeoroni gunicorn[611]:     conn.connect()
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/urllib3/connection.py", line 421, in connect
Nov  1 19:11:03 jukeoroni gunicorn[611]:     tls_in_tls=tls_in_tls,
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/urllib3/util/ssl_.py", line 450, in ssl_wrap_socket
Nov  1 19:11:03 jukeoroni gunicorn[611]:     sock, context, tls_in_tls, server_hostname=server_hostname
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/urllib3/util/ssl_.py", line 493, in _ssl_wrap_socket_impl
Nov  1 19:11:03 jukeoroni gunicorn[611]:     return ssl_context.wrap_socket(sock, server_hostname=server_hostname)
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/usr/lib/python3.7/ssl.py", line 412, in wrap_socket
Nov  1 19:11:03 jukeoroni gunicorn[611]:     session=session
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/usr/lib/python3.7/ssl.py", line 853, in _create
Nov  1 19:11:03 jukeoroni gunicorn[611]:     self.do_handshake()
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/usr/lib/python3.7/ssl.py", line 1117, in do_handshake
Nov  1 19:11:03 jukeoroni gunicorn[611]:     self._sslobj.do_handshake()
Nov  1 19:11:03 jukeoroni gunicorn[611]: urllib3.exceptions.ProtocolError: ('Connection aborted.', ConnectionResetError(104, 'Connection reset by peer'))
Nov  1 19:11:03 jukeoroni gunicorn[611]: During handling of the above exception, another exception occurred:
Nov  1 19:11:03 jukeoroni gunicorn[611]: Traceback (most recent call last):
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/usr/lib/python3.7/threading.py", line 917, in _bootstrap_inner
Nov  1 19:11:03 jukeoroni gunicorn[611]:     self.run()
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/usr/lib/python3.7/threading.py", line 865, in run
Nov  1 19:11:03 jukeoroni gunicorn[611]:     self._target(*self._args, **self._kwargs)
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/django/jukeoroni/player/jukeoroni/juke_box.py", line 336, in track_list_generator_task
Nov  1 19:11:03 jukeoroni gunicorn[611]:     self.create_update_track_list()
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/django/jukeoroni/player/jukeoroni/juke_box.py", line 409, in create_update_track_list
Nov  1 19:11:03 jukeoroni gunicorn[611]:     cover_online = get_album(discogs_client, artist, title_stripped)
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/django/jukeoroni/player/jukeoroni/discogs.py", line 34, in get_album
Nov  1 19:11:03 jukeoroni gunicorn[611]:     if not results:
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/discogs_client/models.py", line 363, in __len__
Nov  1 19:11:03 jukeoroni gunicorn[611]:     return self.count
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/discogs_client/models.py", line 334, in count
Nov  1 19:11:03 jukeoroni gunicorn[611]:     self._load_pagination_info()
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/discogs_client/models.py", line 289, in _load_pagination_info
Nov  1 19:11:03 jukeoroni gunicorn[611]:     data = self.client._get(self._url_for_page(1))
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/discogs_client/client.py", line 113, in _get
Nov  1 19:11:03 jukeoroni gunicorn[611]:     return self._request('GET', url)
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/discogs_client/client.py", line 100, in _request
Nov  1 19:11:03 jukeoroni gunicorn[611]:     content, status_code = self._fetcher.fetch(self, method, url, data=data, headers=headers)
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/discogs_client/fetchers.py", line 145, in fetch
Nov  1 19:11:03 jukeoroni gunicorn[611]:     method, url, data=data, headers=headers, params={'token':self.user_token}
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/discogs_client/utils.py", line 58, in wrapper
Nov  1 19:11:03 jukeoroni gunicorn[611]:     result = f(self, *args, **kwargs)
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/discogs_client/fetchers.py", line 55, in request
Nov  1 19:11:03 jukeoroni gunicorn[611]:     response = request(method=method, url=url, data=data, headers=headers, params=params)
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/requests/api.py", line 61, in request
Nov  1 19:11:03 jukeoroni gunicorn[611]:     return session.request(method=method, url=url, **kwargs)
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/requests/sessions.py", line 542, in request
Nov  1 19:11:03 jukeoroni gunicorn[611]:     resp = self.send(prep, **send_kwargs)
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/requests/sessions.py", line 655, in send
Nov  1 19:11:03 jukeoroni gunicorn[611]:     r = adapter.send(request, **kwargs)
Nov  1 19:11:03 jukeoroni gunicorn[611]:   File "/data/venv/lib/python3.7/site-packages/requests/adapters.py", line 498, in send
Nov  1 19:11:03 jukeoroni gunicorn[611]:     raise ConnectionError(err, request=request)
Nov  1 19:11:03 jukeoroni gunicorn[611]: requests.exceptions.ConnectionError: ('Connection aborted.', ConnectionResetError(104, 'Connection reset by peer'))
    """
    def track_list_generator_thread(self):
        assert self.on, 'turn jukebox on first'
        assert self._track_list_generator_thread is None, '_track_list_generator_thread already running.'
        self._track_list_generator_thread = threading.Thread(target=self.track_list_generator_task)
        self._track_list_generator_thread.name = 'Track List Generator Process'
        self._track_list_generator_thread.daemon = False
        self._track_list_generator_thread.start()

    def track_list_generator_task(self):

        """
Exception in thread Track List Generator Process:
Traceback (most recent call last):
  File "/data/venv/lib/python3.7/site-packages/urllib3/connectionpool.py", line 706, in urlopen
    chunked=chunked,
  File "/data/venv/lib/python3.7/site-packages/urllib3/connectionpool.py", line 382, in _make_request
    self._validate_conn(conn)
  File "/data/venv/lib/python3.7/site-packages/urllib3/connectionpool.py", line 1010, in _validate_conn
    conn.connect()
  File "/data/venv/lib/python3.7/site-packages/urllib3/connection.py", line 421, in connect
    tls_in_tls=tls_in_tls,
  File "/data/venv/lib/python3.7/site-packages/urllib3/util/ssl_.py", line 450, in ssl_wrap_socket
    sock, context, tls_in_tls, server_hostname=server_hostname
  File "/data/venv/lib/python3.7/site-packages/urllib3/util/ssl_.py", line 493, in _ssl_wrap_socket_impl
    return ssl_context.wrap_socket(sock, server_hostname=server_hostname)
  File "/usr/lib/python3.7/ssl.py", line 412, in wrap_socket
    session=session
  File "/usr/lib/python3.7/ssl.py", line 853, in _create
    self.do_handshake()
  File "/usr/lib/python3.7/ssl.py", line 1117, in do_handshake
    self._sslobj.do_handshake()
ConnectionResetError: [Errno 104] Connection reset by peer

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/data/venv/lib/python3.7/site-packages/requests/adapters.py", line 449, in send
    timeout=timeout
  File "/data/venv/lib/python3.7/site-packages/urllib3/connectionpool.py", line 756, in urlopen
    method, url, error=e, _pool=self, _stacktrace=sys.exc_info()[2]
  File "/data/venv/lib/python3.7/site-packages/urllib3/util/retry.py", line 532, in increment
    raise six.reraise(type(error), error, _stacktrace)
  File "/data/venv/lib/python3.7/site-packages/urllib3/packages/six.py", line 769, in reraise
    raise value.with_traceback(tb)
  File "/data/venv/lib/python3.7/site-packages/urllib3/connectionpool.py", line 706, in urlopen
    chunked=chunked,
  File "/data/venv/lib/python3.7/site-packages/urllib3/connectionpool.py", line 382, in _make_request
    self._validate_conn(conn)
  File "/data/venv/lib/python3.7/site-packages/urllib3/connectionpool.py", line 1010, in _validate_conn
    conn.connect()
  File "/data/venv/lib/python3.7/site-packages/urllib3/connection.py", line 421, in connect
    tls_in_tls=tls_in_tls,
  File "/data/venv/lib/python3.7/site-packages/urllib3/util/ssl_.py", line 450, in ssl_wrap_socket
    sock, context, tls_in_tls, server_hostname=server_hostname
  File "/data/venv/lib/python3.7/site-packages/urllib3/util/ssl_.py", line 493, in _ssl_wrap_socket_impl
    return ssl_context.wrap_socket(sock, server_hostname=server_hostname)
  File "/usr/lib/python3.7/ssl.py", line 412, in wrap_socket
    session=session
  File "/usr/lib/python3.7/ssl.py", line 853, in _create
    self.do_handshake()
  File "/usr/lib/python3.7/ssl.py", line 1117, in do_handshake
    self._sslobj.do_handshake()
urllib3.exceptions.ProtocolError: ('Connection aborted.', ConnectionResetError(104, 'Connection reset by peer'))

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/lib/python3.7/threading.py", line 917, in _bootstrap_inner
    self.run()
  File "/usr/lib/python3.7/threading.py", line 865, in run
    self._target(*self._args, **self._kwargs)
  File "/data/django/jukeoroni/player/jukeoroni/juke_box.py", line 432, in track_list_generator_task
    self.create_update_track_list()
  File "/data/django/jukeoroni/player/jukeoroni/juke_box.py", line 514, in create_update_track_list
    else:
  File "/data/django/jukeoroni/player/jukeoroni/discogs.py", line 34, in get_album
    if not results:
  File "/data/venv/lib/python3.7/site-packages/discogs_client/models.py", line 363, in __len__
    return self.count
  File "/data/venv/lib/python3.7/site-packages/discogs_client/models.py", line 334, in count
    self._load_pagination_info()
  File "/data/venv/lib/python3.7/site-packages/discogs_client/models.py", line 289, in _load_pagination_info
    data = self.client._get(self._url_for_page(1))
  File "/data/venv/lib/python3.7/site-packages/discogs_client/client.py", line 113, in _get
    return self._request('GET', url)
  File "/data/venv/lib/python3.7/site-packages/discogs_client/client.py", line 100, in _request
    content, status_code = self._fetcher.fetch(self, method, url, data=data, headers=headers)
  File "/data/venv/lib/python3.7/site-packages/discogs_client/fetchers.py", line 145, in fetch
    method, url, data=data, headers=headers, params={'token':self.user_token}
  File "/data/venv/lib/python3.7/site-packages/discogs_client/utils.py", line 58, in wrapper
    result = f(self, *args, **kwargs)
  File "/data/venv/lib/python3.7/site-packages/discogs_client/fetchers.py", line 55, in request
    response = request(method=method, url=url, data=data, headers=headers, params=params)
  File "/data/venv/lib/python3.7/site-packages/requests/api.py", line 61, in request
    return session.request(method=method, url=url, **kwargs)
  File "/data/venv/lib/python3.7/site-packages/requests/sessions.py", line 542, in request
    resp = self.send(prep, **send_kwargs)
  File "/data/venv/lib/python3.7/site-packages/requests/sessions.py", line 655, in send
    r = adapter.send(request, **kwargs)
  File "/data/venv/lib/python3.7/site-packages/requests/adapters.py", line 498, in send
    raise ConnectionError(err, request=request)
requests.exceptions.ConnectionError: ('Connection aborted.', ConnectionResetError(104, 'Connection reset by peer'))
        """

        _waited = None
        while self.on:
            if not self._auto_update_tracklist:
                _waited = None
            else:
                if _waited is None or _waited % DEFAULT_TRACKLIST_REGEN_INTERVAL == 0:
                    _waited = 0
                    if self._auto_update_tracklist:
                        self.create_update_track_list()
                    # instead of putting it to sleep, we
                    # could schedule it maybe (so that it can finish an
                    # restart at some given time again)
                    # time.sleep(DEFAULT_TRACKLIST_REGEN_INTERVAL)

                _waited += 1
            time.sleep(1.0)

    def create_update_track_list(self):
        # TODO: filter image files, m3u etc.
        LOG.info('Generating updated track list...')
        discogs_client = get_client()
        _files = []
        _albums = []
        _artists = []
        for path, dirs, files in os.walk(MUSIC_DIR):
            if not self.on:
                return
            album = os.path.basename(path)
            try:
                # TODO: maybe use a better character
                artist, year, title = album.split(' - ')
            except ValueError:
                # with open(FAULTY_ALBUMS, 'a+') as f:
                #     f.write(album + '\n')
                # TODO: store this somewhere to fix it
                LOG.exception(f'Not a valid album path: {album}:')
                continue

            cover_online = None
            # TODO: if str(artist).lower() != 'soundtrack':  # Soundtracks have different artists, so no need to add artist cover
            query_artist = Artist.objects.filter(name__exact=artist)
            # TODO: maybe objects.get() is better because artist name is unique
            if bool(query_artist):
                LOG.info(f'Artist {query_artist} found in db...')
                model_artist = query_artist[0]  # name is unique, so index 0 is the correct model
                # if str(model_artist.name).lower() != 'soundtrack':
                if model_artist.cover_online is None:
                    cover_online = get_artist(discogs_client, artist)
                    if cover_online:
                        model_artist.cover_online = cover_online
                        model_artist.save()
            else:
                LOG.info(f'Artist {artist} not found in db; creating new entry...')
                cover_online = get_artist(discogs_client, artist)
                model_artist = Artist(name=artist, cover_online=cover_online)
                model_artist.save()

            if artist not in _artists:
                _artists.append(artist)

            cover_root = path
            jpg_path = os.path.join(cover_root, 'cover.jpg')
            png_path = os.path.join(cover_root, 'cover.png')
            if os.path.exists(jpg_path):
                img_path = jpg_path
            elif os.path.exists(png_path):
                img_path = png_path
            else:
                # with open(MISSING_COVERS_FILE, 'a+') as f:
                #     f.write(cover_root + '\n')
                LOG.info(f'cover is None: {album}')
                img_path = None

            # need to add artist too
            cover_online = None
            title_stripped = title.split(' [')[0]
            query_album = Album.objects.filter(artist=model_artist, album_title__exact=title, year__exact=year)

            if bool(query_album):
                model_album = query_album[0]
                model_album.cover = img_path
                if model_album.cover_online is None:
                    cover_online = get_album(discogs_client, artist, title_stripped)
                    if cover_online:
                        model_album.cover_online = cover_online
            else:
                cover_online = get_album(discogs_client, artist, title_stripped)
                model_album = Album(artist=model_artist, album_title=title, year=year, cover=img_path, cover_online=cover_online)

            try:
                model_album.save()
                _albums.append(album)
            except Exception:
                LOG.exception(f'Cannot save album model {title} by {artist}:')

            for _file in files:
                if not self.on:
                    return
                if os.path.splitext(_file)[1] in AUDIO_FILES:
                    file_path = os.path.join(path, _file)
                    query_track = DjangoTrack.objects.filter(audio_source__exact=file_path)
                    if len(query_track) > 1:
                        LOG.warning(f'Track in DB multiple times: {file_path}')
                        for track in query_track:
                            track.delete()
                            LOG.warning(f'Track deleted: {track}')
                        query_track = []
                    if len(query_track) == 1:
                        LOG.info(f'Track found in DB: {query_track}')
                        _edit = False
                        if not query_track[0].album == model_album:
                            query_track.update(album=model_album)
                            LOG.info('Track album updated in DB: {0}'.format(query_track[0]))
                        if not query_track[0].track_title == _file:
                            query_track.update(track_title=_file)
                            LOG.info('Track track_title updated in DB: {0}'.format(query_track[0]))
                    else:
                        model_track = DjangoTrack.objects.create(album=model_album, audio_source=file_path, track_title=_file)
                        LOG.info('Track created in DB: {0}'.format(model_track))

                    _files.append(file_path)

        # remove obsolete db objects:
        django_tracks = DjangoTrack.objects.all()
        for django_track in django_tracks:
            if django_track.audio_source not in _files:
                LOG.info(f'Removing track from DB: {django_track}')
                django_track.delete()
                LOG.info(f'Track removed from DB: {django_track}')

        django_albums = Album.objects.all()
        for django_album in django_albums:
            occurrences = [i for i in _albums if str(django_album.album_title).lower() in i.lower()]
            # if len(occurrences) > 1:
                # LOG.warning('Multiple albums with same nam')
            if len(occurrences) == 0:
            # if django_album.album_title not in _albums:
            #     LOG.info(django_album.album_title)
            #     LOG.info(_albums)
                LOG.info(f'Removing album from DB: {django_album}')
                django_album.delete()
                LOG.info(f'Album removed from DB: {django_album}')

        django_artists = Artist.objects.all()
        for django_artist in django_artists:
            if django_artist.name not in _artists:
                LOG.info(f'Removing artist from DB: {django_artist}')
                django_artist.delete()
                LOG.info(f'Artist removed from DB: {django_artist}')

        LOG.info(f'Finished: track list generated successfully: {len(_files)} tracks, {len(_albums)} albums and {len(_artists)} artists found')
    ############################################

    ############################################
    # track loader
    # def track_loader_watcher_thread(self):
    #     # this thread makes sure to keep the track loader thread alive
    #     self._track_loader_watcher_thread = threading.Thread(target=self._track_loader_watcher_task)
    #     self._track_loader_watcher_thread.name = 'Track Loader Watcher Thread'
    #     self._track_loader_watcher_thread.daemon = False
    #     self._track_loader_watcher_thread.start()
    #
    # def _track_loader_watcher_task(self):
    #     while self.on:
    #         if self._track_loader_thread is None:
    #             LOG.info('Starting Track Loader Thread...')
    #             self.track_loader_thread()
    #             LOG.info('Track Loader Thread started.')
    #             time.sleep(5.0)
    #         else:
    #             try:
    #                 if self._track_loader_thread.is_alive():
    #                     LOG.debug('Track Loader Thread is up and running.')
    #                     time.sleep(1.0)
    #                     continue
    #             except Exception:
    #                 LOG.info('Seems like Track Loader Thread crashed...')
    #                 self._track_loader_thread = None

    def track_loader_thread(self):
        assert self.on, 'jukebox must be on'
        self._track_loader_thread = threading.Thread(target=self._track_loader_task)
        self._track_loader_thread.name = 'Track Loader Thread'
        self._track_loader_thread.daemon = False
        self._track_loader_thread.start()

    def _track_loader_task(self):
        while self.on:
            LOG.debug(f'{len(self.tracks)} of {MAX_CACHED_FILES} tracks cached. Queue: {self.tracks}')
            # LOG.debug(f'Loading process active: {bool(self.loading_process)}')

            if len(self.tracks) < MAX_CACHED_FILES:
                loading_track = self.get_next_track()
                if loading_track is None:
                    # print(str(next_track))
                    time.sleep(1.0)
                    continue

                self.loading_track = JukeboxTrack(loading_track, cached=True)
                self.loading_track.cache()

                # self.loading_process = None
                if self.loading_track is not None:
                    if not self.loading_track.killed:
                        loading_track_copy = self.loading_track
                        self.tracks.append(loading_track_copy)
                    self.loading_track = None

            time.sleep(1.0)

    @property
    def track_list(self):
        return DjangoTrack.objects.all()

    def get_next_track(self):
        # TODO: we cannot tell which track it is
        #  that is currently being loaded.
        #  because of this, we always have
        #  to start clean, even if the track
        #  is almost fully loaded

        # Random mode
        if self.loader_mode == 'random':
            tracks = self.track_list
            if not bool(tracks):
                return None
            next_track = random.choice(tracks)
            return next_track

        # Album mode
        elif self.loader_mode == 'album':

            if self._need_first_album_track and self.playing_track is not None:
                
                # if we switch mode from Rand to Albm,
                # we always want the first track of
                # the album, no matter what
                track_id = self.playing_track.django_track.id
                album_id = self.playing_track.django_track.album
                album_tracks = DjangoTrack.objects.filter(album=album_id)
                first_track = album_tracks[0]
                first_track_id = first_track.id
                self._need_first_album_track = False
                if track_id != first_track_id:
                    return first_track
                else:
                    # return 2nd track if playing_track is first track of album
                    second_track = album_tracks[1]
                    return second_track

            if self.playing_track is None and not bool(self.tracks) or self.requested_album_id is not None:

                random_album = self.requested_album_id or random.choice(Album.objects.all())
                album_tracks = DjangoTrack.objects.filter(album=random_album)
                next_track = album_tracks[0]
                self.requested_album_id = None
                return next_track

            if bool(self.tracks):
                # TODO: if we pressed the Next button too fast,
                #  self.tracks will be still empty, hence,
                #  we end up here again unintentionally
                # we use this case to append the next track
                # based on the last one in the self.tracks queue
                # i.e: if playing_track has id 1 and self.tracks
                # contains id's [2, 3, 4], we want to append
                # id 5 once a free spot is available
                # in album mode:
                # get next track of album of current track
                previous_track_id = self.tracks[-1].django_track.id
                album = DjangoTrack.objects.get(id=previous_track_id).album

                if self._need_first_album_track:
                    self._need_first_album_track = False
                    album_tracks = DjangoTrack.objects.filter(album=album)
                    first_track = album_tracks[0]
                    first_track_id = first_track.id
                    if first_track_id != previous_track_id:
                        return first_track
                    else:
                        second_track = album_tracks[1]
                        return second_track

                next_track = DjangoTrack.objects.get(id=previous_track_id + 1)

                if next_track.album != album:
                    # choose a new random album if next_track is not part
                    # of current album anymore
                    random_album = random.choice(Album.objects.all())
                    album_tracks = DjangoTrack.objects.filter(album=random_album)
                    next_track = album_tracks[0]

                return next_track

            elif self.playing_track is not None and not bool(self.tracks):
                LOG.info('playing_track {0}'.format(self.playing_track))
                # in case self.tracks is empty, we want the next
                # track id based on the one that is currently
                # playing
                # in album mode:
                # get first track of album of current track
                # if self.tracks is empty, we assume
                # that the first track added to self.tracks must
                # be the first track of the album
                # but we leave the current track playing until
                # it has finished (per default; if we want to skip
                # the currently playing track: "Next" button)
                playing_track_id = self.playing_track.django_track.id
                next_track_id = playing_track_id+1
                next_track = DjangoTrack.objects.get(id=next_track_id)

                album = DjangoTrack.objects.get(id=playing_track_id).album

                if next_track.album != album:
                    random_album = random.choice(Album.objects.all())
                    album_tracks = DjangoTrack.objects.filter(album=random_album)
                    next_track = album_tracks[0]

                return next_track

        return None

    def kill_loading_process(self):
        # if self.loading_track is not None:
            # LOG.info('loading_process: {0}'.format(self.loading_track._))
        # LOG.info('killing self.loading_process and resetting it to None')
        if bool(self.tracks) or \
                not bool(self.tracks) and self.playing_track is not None \
                or self.requested_album_id is not None:
            if self.loading_track is not None:
                LOG.info('loading_process is active, trying to terminate and join...')
                # os.kill(self.process_pid, signal.SIGKILL)
                # TODO try kill()
                self.loading_track.kill_caching_process()
                # self.loading_track.kill()  # SIGKILL
                # # self.loading_process.terminate()  # SIGTERM Does not join
                # LOG.info('loading_process terminated.')
                # self.loading_process.join()
                # LOG.info('loading_process terminated and joined')
                # a process can be joined multiple times:
                # here: just wait for termination before proceeding
                # self.loading_process.join()
            self.loading_track = None

            # remove all cached tracks from the filesystem except the one
            # that is currently playing

            # is it a problem if self.track is still empty?
            for track in self.tracks:
                if track.cached and not track.is_playing:
                    if os.path.exists(track.cache_tmp):
                        try:
                            os.remove(track.cache_tmp)
                        except FileNotFoundError:
                            LOG.exception('Tempfile not found:')
            self.tracks = []
            self._track_loader_thread = None
    ############################################
