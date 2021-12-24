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
    CACHE_TRACKS,
    CACHE_COVERS,
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
        self.path = os.path.join(MUSIC_DIR, self.django_track.audio_source)
        # self.path = u'{0}'.format(str(os.path.join(MUSIC_DIR, self.django_track.audio_source)))
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
        if CACHE_COVERS:
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
            self._cover_album = Image.open(os.path.join(MUSIC_DIR, self.album.cover))
        else:
            LOG.info(f'Offline album cover for Track "{self}" is None...')

        if not COVER_ONLINE_PREFERENCE and self.album.cover is not None:
            LOG.info('Loading offline album cover...')
            self._cover_album = Image.open(os.path.join(MUSIC_DIR, self.album.cover))

        elif COVER_ONLINE_PREFERENCE and self.album.cover_online is not None or self.album.cover is None:
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
        if CACHE_TRACKS:
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
            # LOG.error(self.path)
            # LOG.error(self.path)
            # LOG.error(self.path)
            # LOG.error(self.path)
            # LOG.error(self.path)
            # LOG.error(self.path)
            # LOG.error(self.path)
            # LOG.error(self.path)
            # LOG.error(self.path)
            # LOG.error(self.path)
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
    def __init__(self, jukeoroni=None):

        self.on = False
        self.loader_mode = 'random'

        self.jukeoroni = jukeoroni
        if self.jukeoroni is None:
            LOG.warning('No jukeoroni specified. Functionality is limited.')

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

        self.run_tracklist_generator_flag = False
        self.track_list_updater_running = False

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
                if _waited is None \
                        or _waited % DEFAULT_TRACKLIST_REGEN_INTERVAL == 0\
                        or self.run_tracklist_generator_flag:
                    _waited = 0
                    if self._auto_update_tracklist:
                        self.track_list_updater_running = True
                        self.create_update_track_list()
                    self.run_tracklist_generator_flag = False
                    self.track_list_updater_running = False
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
            # if not self.on:
            #     LOG.warning('JukeBox is turned off.')
            #     return

            # Remove part of path that can be retrieved from settings (MUSIC_DIR)
            # MUSIC_DIR:  /data/usb_hdd/media/audio/music
            # path:       /data/usb_hdd/media/audio/music/on_device/HIM - 2008 - Razorblade Romance [DSD128]/
            _path = os.path.relpath(path, MUSIC_DIR)
            # _path =
            album = os.path.basename(_path)
            try:
                # TODO: maybe use a better character
                artist, year, title = album.split(' - ')
            except ValueError:
                # with open(FAULTY_ALBUMS, 'a+') as f:
                #     f.write(album + '\n')
                # TODO: store this somewhere to fix it
                LOG.exception(f'Not a valid album path: {album}:')
                continue


            # COVER ARTIST
            cover_online = None
            # TODO: if str(artist).lower() != 'soundtrack':  # Soundtracks have different artists, so no need to add artist cover
            query_artist = Artist.objects.filter(name__exact=artist)
            # TODO: maybe objects.get() is better because artist name is unique
            if bool(query_artist):
                LOG.info(f'Artist {query_artist} found in db...')
                model_artist = query_artist[0]  # name is unique, so index 0 is the correct model
                # if str(model_artist.name).lower() != 'soundtrack':
                if model_artist.cover_online is None:
                    LOG.info(f'No online cover for artist {model_artist} defined. Trying to get one...')
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
            # COVER ARTIST

            cover_root = _path
            jpg_path = os.path.join(cover_root, 'cover.jpg')
            png_path = os.path.join(cover_root, 'cover.png')
            if os.path.exists(os.path.join(MUSIC_DIR, jpg_path)):
                img_path = jpg_path
            elif os.path.exists(os.path.join(MUSIC_DIR, png_path)):
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


            # COVER ALBUM
            if bool(query_album):
                model_album = query_album[0]
                LOG.info(f'Album {model_album} found in DB.')
                model_album.cover = img_path
                if model_album.cover_online is None:
                    LOG.info(f'No online cover for album {model_album} defined. Trying to get one...')
                    cover_online = get_album(discogs_client, artist, title_stripped)
                    if cover_online:
                        model_album.cover_online = cover_online
                    else:
                        LOG.info('Could not find an online cover.')
            else:
                cover_online = get_album(discogs_client, artist, title_stripped)
                model_album = Album(artist=model_artist, album_title=title, year=year, cover=img_path, cover_online=cover_online)
                LOG.info(f'Album {model_album} not found in DB.')

            try:
                model_album.save()
                _albums.append(album)
                LOG.info(f'Album {model_album} correctly saved in DB.')
            except Exception:
                LOG.exception(f'Cannot save album model {title} by {artist}:')
            # COVER ALBUM


            for _file in files:
                if os.path.splitext(_file)[1] in AUDIO_FILES:
                    file_path = os.path.join(_path, _file)
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
            if len(occurrences) == 0:
                LOG.info(f'Removing album from DB: {django_album}')
                django_album.delete()
                LOG.info(f'Album removed from DB: {django_album}')

        django_artists = Artist.objects.all()
        for django_artist in django_artists:
            if django_artist.name not in _artists:
                LOG.info(f'Removing artist from DB: {django_artist}')
                django_artist.delete()

                """
AC/DC on OSX (HFS)
ACDC on /data/usb_hdd and AC:DC on /data/googledrive

Dec 19 09:25:01 jukeoroni gunicorn[18042]: Exception in thread Track List Generator Process:
Dec 19 09:25:01 jukeoroni gunicorn[18042]: Traceback (most recent call last):
Dec 19 09:25:01 jukeoroni gunicorn[18042]:   File "/usr/lib/python3.7/threading.py", line 917, in _bootstrap_inner
Dec 19 09:25:01 jukeoroni gunicorn[18042]:     self.run()
Dec 19 09:25:01 jukeoroni gunicorn[18042]:   File "/usr/lib/python3.7/threading.py", line 865, in run
Dec 19 09:25:01 jukeoroni gunicorn[18042]:     self._target(*self._args, **self._kwargs)
Dec 19 09:25:01 jukeoroni gunicorn[18042]:   File "/data/django/jukeoroni/player/jukeoroni/juke_box.py", line 416, in track_list_generator_task
Dec 19 09:25:01 jukeoroni gunicorn[18042]:     self.create_update_track_list()
Dec 19 09:25:01 jukeoroni gunicorn[18042]:   File "/data/django/jukeoroni/player/jukeoroni/juke_box.py", line 562, in create_update_track_list
Dec 19 09:25:01 jukeoroni gunicorn[18042]:     django_artist.delete()
Dec 19 09:25:01 jukeoroni gunicorn[18042]:   File "/data/venv/lib/python3.7/site-packages/django/db/models/base.py", line 953, in delete
Dec 19 09:25:01 jukeoroni gunicorn[18042]:     collector.collect([self], keep_parents=keep_parents)
Dec 19 09:25:01 jukeoroni gunicorn[18042]:   File "/data/venv/lib/python3.7/site-packages/django/db/models/deletion.py", line 308, in collect
Dec 19 09:25:01 jukeoroni gunicorn[18042]:     set(chain.from_iterable(protected_objects.values())),
Dec 19 09:25:01 jukeoroni gunicorn[18042]: django.db.models.deletion.ProtectedError: ("Cannot delete some instances of model 'Artist' because they are referenced through protected foreign keys: 'Album.artist'.", {Back In Black (Master Series V) [DSD128]})
                """

                LOG.info(f'Artist removed from DB: {django_artist}')

        LOG.info(f'Finished: track list generated successfully: {len(_files)} tracks, {len(_albums)} albums and {len(_artists)} artists found')
    ############################################

    ############################################
    # track loader
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

                self.loading_track = JukeboxTrack(loading_track, cached=CACHE_TRACKS)
                self.loading_track.cache()
                self.loading_track.cache_online_covers()

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
        # TODO: it could happen that the file path is not up to date
        #  so a if file does not exist check must be implemented

        next_track = None

        # Random mode
        if self.loader_mode == 'random':
            LOG.info('Getting next track in random mode...')
            tracks = self.track_list
            if not bool(tracks):
                LOG.debug(f'JukeBox tracklist is empty! Returning None.')
                return None
            next_track = random.choice(tracks)
            LOG.info(f'Next track is: {next_track}.')
            return next_track

        # Album mode
        elif self.loader_mode == 'album':
            LOG.info('Getting next track in album mode...')

            if self.requested_album_id is not None:
                LOG.info(f'Next track with specified album id: {self.requested_album_id} ({Album.objects.get(id=self.requested_album_id)})')

                album_tracks = DjangoTrack.objects.filter(album=self.requested_album_id)
                _next_track = JukeboxTrack(album_tracks[0])
                next_track = _next_track.first_album_track
                LOG.info(f'Returning next track: {_next_track}')
                self.requested_album_id = None
                self._need_first_album_track = False

                return next_track

            if self._need_first_album_track:
                LOG.info("First album track requested...")
                self._need_first_album_track = False
                if self.playing_track is not None:
                    LOG.info("Track is playing...")
                    if self.playing_track.is_first_album_track:
                        LOG.info("Currently playing track is first of album. Returning second...")
                        next_track = self.playing_track.next_album_track
                    else:
                        LOG.info("Returning first...")
                        next_track = self.playing_track.first_album_track
                    LOG.info(next_track)
                    return next_track
                else:
                    LOG.info(f'No track is playing.')
                    if bool(self.tracks):
                        # This should never happen as long as the queue gets emptied
                        # by kill_loading_process() FIRST
                        raise NotImplementedError('This case is not implemented.')
                        """
                        LOG.info(f'Queue is not empty. Getting album of first track in queue...')
                        first_in_queue = self.tracks[0]
                        """
                    else:
                        LOG.info(f'Queue is empty. Getting first track of random album...')
                        tracks = self.track_list
                        _next_track = JukeboxTrack(random.choice(tracks))
                        next_track = _next_track.first_album_track
                        LOG.info(f'Next track: {next_track}')
                        return next_track

            else:
                if bool(self.tracks):
                    # This can happen after a mode change if the queue gets filled with
                    # content very quickly after it was emptied

                    LOG.info(f'Getting next track based on queue list...')
                    next_album_track = self.tracks[-1].next_album_track
                    if next_album_track is None:
                        LOG.info(f'Last track in queue is last track of album. Getting first track of random album...')
                        tracks = self.track_list
                        _next_track = JukeboxTrack(random.choice(tracks))
                        next_track = _next_track.first_album_track
                        LOG.info(f'Next track: {next_track}')
                        return next_track
                    else:
                        next_track = next_album_track
                        LOG.info(f'Next track: {next_track}')
                        return next_track

                else:
                    LOG.info(f'Queue list is empty. Getting track based on currently playing...')

                    first_album_track = self.playing_track.first_album_track
                    LOG.info(f'First album track of playing album track is: {first_album_track}')

                    if self.playing_track.django_track == first_album_track:
                        second_album_track = self.playing_track.next_album_track
                        LOG.info(f'Playing track and first track are the same. Returning next: {second_album_track}')
                        return second_album_track
                    else:
                        LOG.info(f'Returing first album track: {first_album_track}')
                        return first_album_track

        LOG.warning('We have an unexpected condition! No next track!')
        assert next_track is not None, 'We have an unexpected condition! No next track!'

    def kill_loading_process(self):
        # TODO: we could implement storing the first track in the queue
        #  that gets emptied here to get stored somewhere so that
        #  we can switch from random to album mode based on the
        #  the first track in the queue if nothing is playing
        #  (track index should suffice)
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
