import glob
import multiprocessing
import os
import logging
import random
import shutil
# import signal
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

    @property
    def cover_album(self):
        # TODO: query Discogs image here on the fly?
        #  downside: we cannot specify the actual image
        #  on the database if path is not stored beforehand
        if self.album.cover_online is not None:
            album_online = Resource().from_url(url=self.album.cover_online)
        else:
            album_online = None

        if self.album.cover is not None:
            cover = Image.open(self.album.cover)
        else:
            cover = Resource().JUKEBOX_ON_AIR_DEFAULT_IMAGE

        if COVER_ONLINE_PREFERENCE:
            return Resource().squareify(album_online) or Resource().squareify(cover)
        else:
            return Resource().squareify(cover) or Resource().squareify(album_online)

    @property
    def cover_artist(self):
        # TODO: query Discogs image here on the fly?
        #  downside: we cannot specify the actual image
        #  on the database if path is not stored beforehand
        if self.artist.cover_online is None:
            return None
        else:
            return Resource().squareify(Resource().from_url(url=self.artist.cover_online))

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
            if self.cached:
                # TODO add to self.__delete__()
                os.remove(self.cache_tmp)
                LOG.info(f'removed from local filesystem: \"{self.cache_tmp}\"')
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

    def turn_on(self):
        assert not self.on, 'Jukebox is already on.'

        self.temp_cleanup()

        self.on = True

        self.track_list_generator_thread()
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
    def track_list_generator_thread(self):
        assert self.on, 'turn jukebox on first'
        assert self._track_list_generator_thread is None, '_track_list_generator_thread already running.'
        self._track_list_generator_thread = threading.Thread(target=self.track_list_generator_task)
        self._track_list_generator_thread.name = 'Track List Generator Process'
        self._track_list_generator_thread.daemon = False
        self._track_list_generator_thread.start()

    def track_list_generator_task(self):
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
        LOG.info('generating updated track list...')
        discogs_client = get_client()
        _files = []
        for path, dirs, files in os.walk(MUSIC_DIR):
            if not self.on:
                return
            album = os.path.basename(path)
            try:
                # TODO: maybe use a better character
                artist, year, title = album.split(' - ')
            except ValueError as err:
                # with open(FAULTY_ALBUMS, 'a+') as f:
                #     f.write(album + '\n')
                # TODO: store this somewhere to fix it
                LOG.exception(f'not a valid album path: {album}: {err}')
                continue

            cover_online = None
            # print(artist)
            query_artist = Artist.objects.filter(name__exact=artist)
            if bool(query_artist):
                model_artist = query_artist[0]
                if model_artist.cover_online is None:
                    cover_online = get_artist(discogs_client, artist)
                    # print(cover_online)
                    if cover_online:
                        model_artist.cover_online = cover_online
                        model_artist.save()
                # print('    artist found in db')
            else:
                cover_online = get_artist(discogs_client, artist)
                # print(cover_online)
                model_artist = Artist(name=artist, cover_online=cover_online)
                model_artist.save()
                # print('    artist created in db')

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
                # print('    album found in db')
            else:
                cover_online = get_album(discogs_client, artist, title_stripped)
                model_album = Album(artist=model_artist, album_title=title, year=year, cover=img_path, cover_online=cover_online)
                # print('    album created in db')

            try:
                model_album.save()
            except Exception as err:
                LOG.exception(f'cannot save album model {title} by {artist}: {err}')

            for _file in files:
                if not self.on:
                    return
                # print('      track: ' + _file)
                if os.path.splitext(_file)[1] in AUDIO_FILES:
                    file_path = os.path.join(path, _file)
                    query_track = DjangoTrack.objects.filter(audio_source__exact=file_path)
                    if len(query_track) > 1:
                        LOG.warning('Track in DB multiple times: {0}'.format(file_path))
                        for track in query_track:
                            track.delete()
                            LOG.warning('Track deleted: {0}'.format(track))
                        query_track = []
                    if len(query_track) == 1:
                        # model_track = query_track
                        LOG.info('Track found in DB: {0}'.format(query_track))
                        _edit = False
                        if not query_track[0].album == model_album:
                            query_track.update(album=model_album)
                            LOG.info('Track album updated in DB: {0}'.format(query_track[0]))
                        if not query_track[0].track_title == _file:
                            query_track.update(track_title=_file)
                            LOG.info('Track track_title updated in DB: {0}'.format(query_track[0]))
                        # model_track.save()

                        # print('        track found in db')
                    else:
                        model_track = DjangoTrack.objects.create(album=model_album, audio_source=file_path, track_title=_file)
                        LOG.info('Track created in DB: {0}'.format(model_track))
                        # model_track.save()
                        # print('        track created in db')

                    _files.append(file_path)

        # remove obsolete db objects:
        django_tracks = DjangoTrack.objects.all()
        for django_track in django_tracks:
            if django_track.audio_source not in _files:
                django_track.delete()
                LOG.info(f'Track removed from DB: {django_track}')

        LOG.info(f'Fished: track list generated successfully: {len(_files)} tracks found')
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
