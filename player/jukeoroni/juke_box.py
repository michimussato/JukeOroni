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
    MISSING_COVERS_FILE,
    COVER_ONLINE_PREFERENCE,
    FAULTY_ALBUMS,
    DEFAULT_TRACKLIST_REGEN_INTERVAL,
    MODES,
    FFPLAY_CMD,
)
from player.models import Album

LOG = logging.getLogger(__name__)
LOG.setLevel(GLOBAL_LOGGING_LEVEL)


class Process(multiprocessing.Process):
    def __init__(self, *args, **kwargs):
        super(Process, self).__init__(*args, **kwargs)
        self.track = kwargs['kwargs']['track']


class JukeboxTrack(object):
    def __init__(self, django_track, cached=True):
        self.django_track = django_track
        self.path = self.django_track.audio_source
        self.cached = cached
        self.cache = None
        self.playing_proc = None

        if self.cached:
            self._cache()

    @property
    def track_title(self):
        return self.path.split(os.sep)[-1]

    @property
    def album(self):
        return Album.objects.get(track=self.django_track)

    @property
    def artist(self):
        return self.album.artist_id

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
            return album_online or cover
        else:
            return cover or album_online

    @property
    def cover_artist(self):
        # TODO: query Discogs image here on the fly?
        #  downside: we cannot specify the actual image
        #  on the database if path is not stored beforehand
        artist_online = Resource().from_url(url=self.artist.cover_online)
        return artist_online

    @property
    def media_info(self):
        return mediainfo(self.path)

    def _cache(self):
        self.cache = tempfile.mkstemp()[1]
        LOG.info(f'copying to local filesystem: \"{self.path}\" as \"{self.cache}\"')
        shutil.copy(self.path, self.cache)

    @property
    def playing_from(self):
        return self.cache if self.cached else self.path

    @property
    def is_playing(self):
        return bool(self.playing_proc)

    # @property
    # def next_track(self):
    #     while not bool(self.tracks)
    #     return self

    def play(self, jukeoroni):
        try:
            LOG.info(f'starting playback: \"{self.path}\" from: \"{self.playing_from}\"')
            # self.django_track.played += 1
            # self.django_track.save()
            jukeoroni.playback_proc = subprocess.Popen(FFPLAY_CMD + [self.playing_from], shell=False)
            jukeoroni.set_mode_jukebox()
            jukeoroni.playback_proc.communicate()
            # jukeoroni._playback_thread.join()
            LOG.info(f'playback finished: \"{self.path}\"')
            self.django_track.played += 1
            self.django_track.save()
        except Exception:
            LOG.exception('playback failed: \"{0}\"'.format(self.path))
        finally:
            # jukeoroni.playback_proc = None
            if self.cached:
                os.remove(self.cache)
                LOG.info(f'removed from local filesystem: \"{self.cache}\"')
            jukeoroni.playback_proc = None
            # jukeoroni.next(media=)


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
        # self.set_mode_standby_random()

        self.jukeoroni = jukeoroni

        self.layout = JukeboxLayout()

        self.playing_track = None
        self.is_on_air = None

        self.requested_album_id = None
        self._need_first_album_track = False
        self._auto_update_tracklist = False

        self.loading_queue = multiprocessing.Queue()
        self.tracks = []
        self.loading_process = None

        self._track_list_generator_thread = None
        self._track_loader_thread = None

    @property
    def next_track(self):
        if not bool(self.tracks):
            return None
        return self.tracks.pop(0)

    def turn_on(self):
        assert not self.on, 'Jukebox is already on.'
        self.on = True

        self.set_loader_mode_random()

        self.track_list_generator_thread()
        self.track_loader_thread()

    def turn_off(self):
        assert self.on, 'Jukebox is already off.'
        self.on = False
        if self._track_list_generator_thread is not None:
            self._track_list_generator_thread.join()
            self._track_list_generator_thread = None

    ############################################
    # set modes
    def set_loader_mode_random(self):
        self.loader_mode = 'random'

    def set_loader_mode_album(self):
        self.loader_mode = 'album'
        self._need_first_album_track = True

    # def set_mode_standby_random(self):
    #     self.mode = MODES['jukebox']['standby_random']
    #
    # def set_mode_standby_album(self):
    #     self.mode = MODES['jukebox']['standby_album']
    #
    # def set_mode_on_air_random(self):
    #     self.mode = MODES['jukebox']['on_air_random']
    #
    # def set_mode_on_air_album(self):
    #     self.mode = MODES['jukebox']['on_air_album']
    # ############################################

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
            query_album = Album.objects.filter(artist_id=model_artist, album_title__exact=title, year__exact=year)

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
                model_album = Album(artist_id=model_artist, album_title=title, year=year, cover=img_path, cover_online=cover_online)
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
                    if bool(query_track):
                        model_track = query_track[0]

                        # print('        track found in db')
                    else:
                        model_track = DjangoTrack(album_id=model_album, audio_source=file_path)
                        model_track.save()
                        # print('        track created in db')

                    _files.append(file_path)

        # remove obsolete db objects:
        django_tracks = DjangoTrack.objects.all()
        for django_track in django_tracks:
            if django_track.audio_source not in _files:
                django_track.delete()

        LOG.info(f'track list generated successfully: {len(_files)} tracks found')
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
            if len(self.tracks) + int(bool(self.loading_process)) < MAX_CACHED_FILES and not bool(self.loading_process):
                next_track = self.get_next_track()
                if next_track is None:
                    time.sleep(1.0)
                    continue

                # threading approach seems causing problems if we actually need to empty
                # self.tracks. the thread will finish and add the cached track to self.tracks
                # afterwards because we cannot kill the running thread

                # multiprocessing approach
                # this approach apparently destroys the Track object that it uses to cache
                # data. when the Queue handles over that cached object, it seems like
                # it re-creates the Track object (pickle, probably) but the cached data is
                # gone of course because __del__ was called before that already.
                self.loading_process = Process(target=self._load_track_task, kwargs={'track': next_track})
                # print(dir(self.loading_process))
                # print(self.loading_process.__dict__)
                # print(self.loading_process._kwargs['track'])
                self.loading_process.name = 'Track Loader Task Process'
                self.loading_process.start()

                self.loading_process.join()
                if self.loading_process is not None:
                    # self.loading_process waits for a result
                    # which it won't receive in case we killed
                    # the loading process (mode switch), so
                    # we would get stuck here if self.loading_process
                    # was None
                    ret = self.loading_queue.get()

                    if self.loading_process.exitcode:
                        raise Exception('Exit code not 0')

                    if ret is not None:
                        self.tracks.append(ret)

                self.loading_process = None

            time.sleep(1.0)

    # @property
    # def loading_process_track(self):
    #     if self.loading_process is None:
    #         return None
    #     else:
    #         return self.loading_process._kwargs['track']

    def _load_track_task(self, **kwargs):
        track = kwargs['track']
        LOG.debug(f'starting thread: \"{track.audio_source}\"')

        try:
            size = os.path.getsize(track.audio_source)
            LOG.info(f'loading track ({str(round(size / (1024*1024), 3))} MB): \"{track.audio_source}\"')
            processing_track = JukeboxTrack(track)
            LOG.info(f'loading successful: \"{track.audio_source}\"')
            ret = processing_track
        except MemoryError as err:
            LOG.exception(f'loading failed: \"{track.audio_source}\": {err}')
            ret = None

        # here, or after that, probably processing_track.__del__() is called but pickled/recreated
        # in the main process
        self.loading_queue.put(ret)

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
        # if self.mode == MODES['jukebox']['on_air_random'] or \
        #         self.mode == MODES['jukebox']['standby_random'] or \
        #         True:  # TODO remove later
        # if self.jukeoroni.mode == MODES['jukebox']['standby_random'] or \
        #     self.jukeoroni.mode == MODES['jukebox']['on_air_random']:
        if self.loader_mode == 'random':
            tracks = self.track_list
            if not bool(tracks):
                return None
            next_track = random.choice(tracks)
            return next_track

        # Album mode
        elif self.loader_mode == 'album':

            # raise NotImplementedError

            if self._need_first_album_track and self.playing_track is not None:
                # if we switch mode from Rand to Albm,
                # we always want the first track of
                # the album, no matter what
                track_id = self.playing_track.track.id
                album_id = self.playing_track.track.album_id
                album_tracks = DjangoTrack.objects.filter(album_id=album_id)
                first_track = album_tracks[0]
                first_track_id = first_track.id
                self._need_first_album_track = False
                if track_id != first_track_id:
                    return first_track

            if self.playing_track is None and not bool(self.tracks):
                if bool(self.loading_process):
                    self.kill_loading_process()
                random_album = self.requested_album_id or random.choice(Album.objects.all())
                album_tracks = DjangoTrack.objects.filter(album_id=random_album)
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
                previous_track_id = self.tracks[-1].track.id
                album = DjangoTrack.objects.get(id=previous_track_id).album_id

                next_track = DjangoTrack.objects.get(id=previous_track_id + 1)

                if next_track.album_id != album:
                    # choose a new random album if next_track is not part
                    # of current album anymore
                    random_album = random.choice(Album.objects.all())
                    album_tracks = DjangoTrack.objects.filter(album_id=random_album)
                    next_track = album_tracks[0]

                return next_track

            elif self.playing_track is not None and not bool(self.tracks):
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
                playing_track_id = self.playing_track.track.id
                next_track_id = playing_track_id+1
                next_track = DjangoTrack.objects.get(id=next_track_id)

                album = DjangoTrack.objects.get(id=playing_track_id).album_id

                if next_track.album_id != album:
                    random_album = random.choice(Album.objects.all())
                    album_tracks = DjangoTrack.objects.filter(album_id=random_album)
                    next_track = album_tracks[0]

                return next_track

        return None
        # raise Exception('we should not be here, no next track!!!')

    def kill_loading_process(self):
        LOG.info('killing self.loading_process and resetting it to None')
        if self.loading_process is not None:
            self.loading_process.terminate()
            # a process can be joined multiple times:
            # here: just wait for termination before proceeding
            # self.loading_process.join()
        self.loading_process = None

        # remove all cached tracks from the filesystem except the one
        # that is currently playing

        # is it a problem if self.track is still empty?
        for track in self.tracks:
            if track.cached and not track.is_playing:
                os.remove(track.cache)
        self.tracks = []
    ############################################

