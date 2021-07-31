import os
# import urllib2 as urllib
import io
import sys
import glob
import random
import time
# import requests
import urllib.request
from pydub.utils import mediainfo
import threading
import subprocess
import multiprocessing
import logging
from inky.inky_uc8159 import Inky, BLACK
import signal
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
import shutil
import tempfile
from django.utils.timezone import localtime, now
from .models import Track as DjangoTrack
from .models import Artist
from .models import Album
from .models import Channel as DjangoChannel
from .displays import Standby as StandbyLayout
from .displays import Player as PlayerLayout


LOG = logging.getLogger(__name__)

MEDIA_ROOT = r'/data/googledrive/media/audio/'
CACHE_FILE = os.path.join(MEDIA_ROOT, 'music_cache_test.txt')
MISSING_COVERS_FILE = os.path.join(MEDIA_ROOT, 'missing_covers_test.txt')
FAULTY_ALBUMS = os.path.join(MEDIA_ROOT, 'faulty_albums_test.txt')
MUSIC_DIR = os.path.join(MEDIA_ROOT, 'music')
MAX_CACHED_FILES = 3
PIMORONI_SATURATION = 1.0
PIMORONI_SIZE = 600, 448
FONT_SIZE = 20
SLEEP_IMAGE = '/data/django/jukeoroni/player/static/zzz.jpg'
LOADING_IMAGE = '/data/django/jukeoroni/player/static/loading.jpg'
STANDARD_COVER = '/data/django/jukeoroni/player/static/cover_std.png'
PIMORONI_FONT = '/data/django/jukeoroni/player/static/gotham-black.ttf'
DEFAULT_TRACKLIST_REGEN_INTERVAL = 12  # in hours
CLOCK_UPDATE_INTERVAL = 5  # in minutes

# buttons setup
BUTTONS = [5, 6, 16, 24]

# Toggles:
# https://stackoverflow.com/questions/8381735/how-to-toggle-a-value
BUTTON_1 = {
            #'Albm': 'Rand',
            #'    Albm    ': 'Rand',
            'Albm -> Rand': 'Rand -> Albm',
            # #'Rand': 'Sequ',
            # 'Rand -> Sequ': 'Sequ -> Albm',
            #'Sequ': 'Albm',
            'Rand -> Albm': 'Albm -> Rand',
            }
BUTTON_2 = {
            'Stop': 'Stop',
            }
BUTTON_3 = {
            'Next': 'Play',
            'Play': 'Next'
            }
BUTTON_4 = {
            # 'Stop': 'Strm',
            'Strm': 'Strm',
            # 'back': 'Back',
            }

# Button   4       3       2       1
# LABELS = ['Stop', 'Next', 'Play', 'Radio']

# for portrait orientation, the order is reversed
# LABELS = [BUTTON_4, BUTTON_3, BUTTON_2, BUTTON_1]

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# Audio files to index:
AUDIO_FILES = ['.dsf', '.flac', '.wav', '.dff']


class Track(object):
    def __init__(self, track, cached=True):
        self.track = track
        self.path = self.track.audio_source
        self.cached = cached
        self.cache = None
        self.is_playing = False

        if self.cached:
            self._cache()

    @property
    def cover(self):
        album = Album.objects.get(track=self.track)
        return album.cover

    @property
    def media_info(self):
        return mediainfo(self.path)

    def _cache(self):
        self.cache = tempfile.mkstemp()[1]
        logging.info(f'copying to local filesystem: \"{self.path}\" as \"{self.cache}\"')
        print(f'copying to local filesystem: \"{self.path}\" as \"{self.cache}\"')
        shutil.copy(self.path, self.cache)

    @property
    def playing_from(self):
        return self.cache if self.cached else self.path

    def play(self):
        try:
            # ffplay -threads
            logging.info(f'starting playback: \"{self.path}\" from: \"{self.playing_from}\"')
            print(f'starting playback: \"{self.path}\" from: \"{self.playing_from}\"')
            self.track.played += 1
            self.track.save()
            self.is_playing = True
            print(multiprocessing.current_process().pid)
            # TODO: now this would be a classic
            #  subprocess example: calling an external
            #  application
            os.system(f'ffplay -hide_banner -autoexit -vn -nodisp -loglevel error \"{self.playing_from}\"')
            logging.info(f'playback finished: \"{self.path}\"')
            print(f'playback finished: \"{self.path}\"')
        except Exception as err:
            print(err)
            logging.exception('playback failed: \"{0}\"'.format(self.path))
            print('playback failed: \"{0}\"'.format(self.path))
        finally:
            self.is_playing = False
            if self.cached:
                os.remove(self.cache)
                logging.info(f'removed from local filesystem: \"{self.cache}\"')
                print(f'removed from local filesystem: \"{self.cache}\"')


class Player(object):

    def __init__(self, auto_update_tracklist=False):
        logging.info('initializing player...')
        print('initializing player...')
        # assert state in LABELS, "state should be one of {0}".format(LABELS)
        self.button_1_value = BUTTON_1['Albm -> Rand']
        self.button_2_value = BUTTON_2['Stop']
        self.button_3_value = BUTTON_3['Next']
        self.button_4_value = BUTTON_4['Strm']

        self.auto_update_tracklist = auto_update_tracklist
        self.tracks = []
        self.loading = 0
        self.loading_queue = multiprocessing.Queue()
        self.loading_process = None
        self.playing = False
        self.playing_track = None
        self.sequential = False
        self._quit = False
        self.pimoroni = Inky()
        self.pimoroni.set_border('BLACK')

        self.current_time = None
        self.channel_streaming = None

        self.layout_standby = StandbyLayout()
        self.layout_player = PlayerLayout()

        self._pimoroni_thread = None
        self._playback_thread = None
        self._buttons_watcher_thread = None
        self._track_loader_thread = None
        self._pimoroni_watcher_thread = None
        self._state_watcher_thread = None
        self._track_list_generator_thread = None

        logging.info('player initialized.')
        print('player initialized.')

    def temp_cleanup(self):
        temp_dir = tempfile.gettempdir()
        logging.info(f'cleaning up {temp_dir}...')
        print(f'cleaning up {temp_dir}...')
        for filename in glob.glob(os.path.join(temp_dir, 'tmp*')):
            os.remove(filename)
        logging.info('cleanup done.')
        print('cleanup done.')

    @property
    def LABELS(self):
        return [self.button_1_value, self.button_2_value, self.button_3_value, self.button_4_value]

    ############################################
    # buttons
    def buttons_watcher_thread(self):
        self._buttons_watcher_thread = threading.Thread(target=self._buttons_watcher_task)
        self._buttons_watcher_thread.name = 'Buttons Watcher Thread'
        self._buttons_watcher_thread.daemon = False
        self._buttons_watcher_thread.start()

    def _buttons_watcher_task(self):
        for pin in BUTTONS:
            GPIO.add_event_detect(pin, GPIO.FALLING, self._handle_button, bouncetime=250)
        signal.pause()

    def _handle_button(self, pin):
        current_label = self.LABELS[BUTTONS.index(pin)]
        logging.info(f"Button press detected on pin: {pin} label: {current_label}")
        print(f"Button press detected on pin: {pin} label: {current_label}")

        # # just kill the radio in every case:
        # # (radical for now)
        # pid = subprocess.Popen(['pidof mplayer'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # pid_output = pid.communicate()[0].decode('utf-8').replace('\n', '')
        # if pid_output != '':
        #     os.system(f'kill {pid_output}')

        # Mode button
        if self.button_3_value == 'Next':  # we only want to switch mode when something is already playing
            if current_label == self.button_1_value:
                # empty cached track list but leave current track playing
                # but update the display to reflect current Mode
                self.kill_loading_process()

                self.button_1_value = BUTTON_1[current_label]

                self.set_image(track=self.playing_track)
                print(f'Playback mode is now {self.button_1_value}.')
                logging.info(f'Playback mode is now {self.button_1_value}.')
                return

        # Stop button
        if current_label == self.button_2_value:
            if self._playback_thread is not None:
                print('Playback stopped.')
                logging.info('Playback stopped.')
                self.button_3_value = BUTTON_3['Next']  # Switch button back to Play
                self.stop()
                # self.kill_loading_process()
                self.set_image()

        # Play/Next button
        if current_label == self.button_3_value:
            if current_label == 'Play':
                print('Starting playback.')
                logging.info('Starting playback.')
                self.button_3_value = BUTTON_3[current_label]
            elif current_label == 'Next':
                print('Next track.')
                logging.info('Next track.')
                self.next()

        # Radio button
        if current_label == self.button_4_value:
            # Album.objects.all()
            if False:
            # if self.button_3_value == 'Next':
                print('we are in playback mode. stop first.')
                return
            else:
                try:
                    self.stop()
                    channels = DjangoChannel.objects.all()
                    last_channel = random.choice(channels)
                    # for channel in channels:
                    #     if channel.last_played:
                    #         last_channel = channel
                    #         break
                    # subprocess.Popen(
                    #     ['mplayer', '-nogui', '-noconfig', 'all', '-novideo', '-nocache', '-playlist', last_channel.url])

                    image_file_url = last_channel.url_logo

                    if image_file_url is not None and image_file_url.startswith('http'):
                        if image_file_url.startswith('http'):
                            print(f'Getting cover from {image_file_url}')
                            img = io.BytesIO(urllib.request.urlopen(image_file_url).read())
                            cover = Image.open(img)
                            # cover = Image.open(requests.get(image_file_url, stream=True).raw)
                        else:
                            cover = Image.open(image_file_url, 'r')
                        self.set_image(image_file=cover)
                    else:
                        # cover = Image.open(image_file_url, 'r')
                        self.set_image(image_file=STANDARD_COVER)
                    # cover = Image.open(requests.get(image_file_url, stream=True).raw)

                    # self.set_image(image_file=cover)
                    # bg = self.layout_player.get_layout(labels=self.LABELS, cover=cover)

                except DjangoChannel.DoesNotExist:
                    return
            return
    ############################################

    ############################################
    # track list generator
    # this is not returning non picklable objects
    # so hopefully ideal for multiprocessing
    def track_list_generator_thread(self, **kwargs):
        self._track_list_generator_thread = multiprocessing.Process(target=self.track_list_generator_task, kwargs=kwargs)
        self._track_list_generator_thread.name = 'Track List Generator Process'
        self._track_list_generator_thread.daemon = False
        self._track_list_generator_thread.start()

    def track_list_generator_task(self, **kwargs):
        while True and not self._quit:
            if self.auto_update_tracklist:
                self.create_update_track_list()
            # instead of putting it to sleep, we
            # could schedule it (so that it can finish an
            # restart at some given time again)
            time.sleep(kwargs.get('auto_update_tracklist_interval') or DEFAULT_TRACKLIST_REGEN_INTERVAL/3600)  # is 12 hours

    @staticmethod
    def create_update_track_list():
        # TODO: filter image files, m3u etc.
        logging.info('generating updated track list...')
        print('generating updated track list...')
        _files = []
        for path, dirs, files in os.walk(MUSIC_DIR):
            album = os.path.basename(path)
            try:
                # TODO: maybe use a better character
                artist, year, title = album.split(' - ')
            except ValueError as err:
                with open(FAULTY_ALBUMS, 'a+') as f:
                    f.write(album + '\n')
                # TODO: store this somewhere to fix it
                print(err)
                LOG.exception(f'not a valid album path: {album}')
                print(f'not a valid album path: {album}')
                continue

            query_artist = Artist.objects.filter(name__exact=artist)
            if bool(query_artist):
                model_artist = query_artist[0]
                # print('    artist found in db')
            else:
                model_artist = Artist(name=artist)
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
                with open(MISSING_COVERS_FILE, 'a+') as f:
                    f.write(cover_root + '\n')
                logging.info(f'cover is None: {album}')
                print(f'cover is None: {album}')
                img_path = None

            # need to add artist too
            query_album = Album.objects.filter(artist_id=model_artist, album_title__exact=title, year__exact=year)

            if bool(query_album):
                model_album = query_album[0]
                model_album.cover = img_path
                # print('    album found in db')
            else:
                model_album = Album(artist_id=model_artist, album_title=title, year=year, cover=img_path)
                # print('    album created in db')

            try:
                model_album.save()
            except Exception as err:
                logging.exception(err)
                print(err)

            for _file in files:
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

        logging.info(f'track list generated successfully: {len(_files)} tracks found')
        print(f'track list generated successfully: {len(_files)} tracks found')
    ############################################

    ############################################
    # track loader
    def track_loader_thread(self):
        self._track_loader_thread = threading.Thread(target=self._track_loader_task)
        self._track_loader_thread.name = 'Track Loader Thread'
        self._track_loader_thread.daemon = False
        self._track_loader_thread.start()

    def _track_loader_task(self):
        while True and not self._quit:
            if len(self.tracks) + self.loading < MAX_CACHED_FILES and not bool(self.loading):
                next_track = self.get_next_track()
                if next_track is None:
                    time.sleep(1.0)
                    continue

                # # threading approach seems causing problems if we actually need to empty
                # # self.tracks. the thread will finish and add the cached track to self.tracks
                # # afterwards because we cannot kill the running thread
                # thread = threading.Thread(target=self._load_track_task, kwargs={'track': next_track})
                # # TODO: maybe this name is not ideal
                # thread.name = 'Track Loader Task Thread'
                # thread.daemon = False

                # multiprocessing approach
                # this approach apparently destroys the Track object that it uses to cache
                # data. when the Queue handles over that cached object, it seems like
                # it re-creates the Track object (pickle, probably) but the cached data is
                # gone of course because __del__ was called before that already.
                self.loading_process = multiprocessing.Process(target=self._load_track_task, kwargs={'track': next_track})
                self.loading_process.name = 'Track Loader Task Process'
                self.loading_process.start()

                self.loading += 1

                # if self.loading_process is not None:
                # stop here and wait for the process to finish or to get killed
                # in case of a mode change
                self.loading_process.join()
                ret = self.loading_queue.get()

                if ret is not None:
                    self.tracks.append(ret)

                self.loading -= 1

            time.sleep(1.0)

    def _load_track_task(self, **kwargs):
        track = kwargs['track']
        logging.debug(f'starting thread: \"{track.audio_source}\"')
        print(f'starting thread: \"{track.audio_source}\"')

        try:
            size = os.path.getsize(track.audio_source)
            logging.info(f'loading track ({str(round(size / (1024*1024), 3))} MB): \"{track.audio_source}\"')
            print(f'loading track ({str(round(size / (1024*1024), 3))} MB): \"{track.audio_source}\"')
            processing_track = Track(track)
            logging.info(f'loading successful: \"{track.audio_source}\"')
            print(f'loading successful: \"{track.audio_source}\"')
            ret = processing_track
        except MemoryError as err:
            print(err)
            logging.exception(f'loading failed: \"{track.audio_source}\"')
            print(f'loading failed: \"{track.audio_source}\"')
            ret = None

        # here, or after that, probably processing_track.__del__() is called but pickled/recreated
        # in the main process
        self.loading_queue.put(ret)
    ############################################

    ############################################
    # Pimoroni
    def pimoroni_watcher_thread(self):
        self._pimoroni_watcher_thread = threading.Thread(target=self._pimoroni_watcher_task)
        self._pimoroni_watcher_thread.name = 'Pimoroni Watcher Thread'
        self._pimoroni_watcher_thread.daemon = False
        self._pimoroni_watcher_thread.start()

    def _pimoroni_watcher_task(self):
        while True:
            if self._pimoroni_thread is not None:
                thread = self._pimoroni_thread
                self._pimoroni_thread = None
                if not thread.is_alive():
                    thread.start()

                while thread.is_alive():
                    time.sleep(1.0)

            time.sleep(1.0)
    ############################################

    ############################################
    # State watcher (buttons)
    def state_watcher_thread(self):
        self._state_watcher_thread = threading.Thread(target=self.state_watcher_task)
        self._state_watcher_thread.name = 'State Watcher Thread'
        self._state_watcher_thread.daemon = False
        self._state_watcher_thread.start()

    def state_watcher_task(self):
        while True and not self._quit:

            new_time = localtime(now())

            if self.button_3_value == 'Next':  # equals: in Play mode
                # TODO implement Play/Next combo
                if self._playback_thread is None:
                    self.play()
                elif self._playback_thread.is_alive():
                    pass

            # elif self.button_4_value == ''

            elif self.current_time != new_time.strftime('%H:%M'):  # in stopped state
                if self.current_time is None or (int(new_time.strftime('%H:%M')[-2:])) % CLOCK_UPDATE_INTERVAL == 0:
                    self.set_image()
                    # set_display(standby)
                    self.current_time = new_time.strftime('%H:%M')

            time.sleep(1.0)

        self.quit()
    ############################################

    ############################################
    # Playback
    def play(self):
        self.playback_thread()

    def playback_thread(self):
        printed_waiting_msg = False
        while not self.tracks and not self.loading:
            if not printed_waiting_msg:
                logging.info('waiting for loading thread to kick in')
                print('waiting for loading thread to kick in')
                printed_waiting_msg = True
            time.sleep(1)

        del printed_waiting_msg

        _display_loading = False
        while not self.tracks and self.loading:
            if not _display_loading:
                # self.layout_player.get_layout(labels=self.LABELS, cover=LOADING_IMAGE)
                self.set_image(image_file=LOADING_IMAGE)
                _display_loading = True

                print('loading 1st track')
                logging.info('loading 1st track')
            time.sleep(1.0)

        print('loading 1st track finished')
        logging.info('loading 1st track finished')

        del _display_loading

        if self.tracks:
            track = self.tracks.pop(0)

            # print(track)
            # print(track)
            # print(track)
            # print(track)

            # cannot use multithreading.Process because the target wants
            # to modify self.playing_track. only works with threading.Thread
            self._playback_thread = threading.Thread(target=self._playback_task, kwargs={'track': track})
            self._playback_thread.name = 'Playback Thread'
            self._playback_thread.daemon = False
            self._playback_thread.start()

            # start playback first, then change image to prevent lag
            self.set_image(track=track)
            # print('here')
            # print(self._playback_thread)
            # <Process(Playback Thread, started)>
            # print(self.playing_track)
            # print(self.playing_track)
            # print(self.playing_track)
            # print(self.playing_track)
            self._playback_thread.join()
            # print(self.playing_track)
            # print(self.playing_track)
            # print(self.playing_track)
            # print(self.playing_track)

            # print(self._playback_thread)
            # <Process(Playback Thread, stopped)>

            # so, join continues as soon as this
            # thread is finished, leaving the rest
            # of the application responsive
            # print('there')
            self.playing_track = None
            self._playback_thread = None
            print(self._playback_thread)
            # None

    def _playback_task(self, **kwargs):
        print(multiprocessing.current_process().pid)
        self.playing_track = kwargs['track']
        logging.debug(f'starting playback thread: for {self.playing_track.path} from {self.playing_track.playing_from}')  # TODO add info
        print(f'starting playback thread: for {self.playing_track.path} from {self.playing_track.playing_from}')  # TODO add info
        self.playing_track.play()

        # cleanup
        # self._playback_thread.close()
        # self.playing_track = None
        # self._playback_thread = None
    ############################################

    def kill_loading_process(self):
        print('killing self.loading_process and resetting it to None')
        if self.loading_process is not None:
            self.loading_process.terminate()
            # a process can be joined multiple times:
            # here: just wait for termination before proceeding
            self.loading_process.join()
        self.loading_process = None
        # remove all cached tracks from the filesystem except the one
        # that is currently playing
        for track in self.tracks:
            if track.cached and not track.is_playing:
                os.remove(track.cache)
        self.tracks = []

    def __del__(self):
        # TODO: when we do sudo systemctl restart apache2
        #  the song stops, but the next one starts to play
        #  until the running thread gets killed
        self.quit()

    def quit(self):
        self._quit = True

        self._track_list_generator_thread = None
        self._pimoroni_thread = None
        self._playback_thread = None
        self._buttons_watcher_thread = None
        self._track_loader_thread = None
        self._pimoroni_watcher_thread = None
        self._state_watcher_thread = None

        while self.tracks:
            self.tracks.pop(0)

        sys.exit(0)

    def task_pimoroni_set_image(self, **kwargs):
        if self.button_3_value != 'Next':
            bg = self.layout_standby.get_layout(labels=self.LABELS)
        else:
            cover = STANDARD_COVER
            if 'image_file' in kwargs:
                cover = kwargs['image_file']
            elif 'track' in kwargs:
                if kwargs['track'] is not None:
                    cover = kwargs['track'].cover

            bg = self.layout_player.get_layout(labels=self.LABELS, cover=cover)

        self.pimoroni.set_image(bg, saturation=PIMORONI_SATURATION)
        self.pimoroni.show(busy_wait=False)

    def buttons_img_overlay(self, bg):
        buttons_img = Image.new(mode='RGB', size=(448, 12), color=(0, 0, 0))
        buttons_draw = ImageDraw.Draw(buttons_img)
        buttons_draw.text((0, 0), '       {0}               {1}               {2}           {3}'.format(
            self.button_4_value,
            self.button_3_value,
            self.button_2_value,
            self.button_1_value,
        ), fill=(255, 255, 255))
        bg.paste(buttons_img, (0, 0))

    @property
    def track_list(self):
        return DjangoTrack.objects.all()

    def get_next_track(self):
        next_track = None
        if self.button_1_value == 'Rand -> Albm':
            tracks = self.track_list
            if not bool(tracks):
                return None
            next_track = random.choice(tracks)

        elif self.button_1_value == 'Albm -> Rand':

            tracks = self.track_list
            if not bool(tracks):
                return None
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

                # album_tracks = Track.objects.filter(album_id=album)
                next_track = DjangoTrack.objects.get(id=previous_track_id + 1)

                if next_track.album_id != album:
                    # choose a new random album if next_track is not part
                    # of current album anymore
                    random_album = random.choice(Album.objects.all())
                    album_tracks = DjangoTrack.objects.filter(album_id=random_album)
                    next_track = album_tracks[0]

            else:
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
                previous_track_id = self.playing_track.track.id

                """
                [Sat Jul 31 17:26:00.947039 2021] [wsgi:error] [pid 27170:tid 2835346464] Button press detected on pin: 5 label: Rand -> Albm
                [Sat Jul 31 17:26:01.169609 2021] [wsgi:error] [pid 27170:tid 2805986336] 'NoneType' object has no attribute 'is_alive'
                [Sat Jul 31 17:26:01.183415 2021] [wsgi:error] [pid 27170:tid 2835346464] Playback mode is now Albm -> Rand.
                [Sat Jul 31 17:26:02.678782 2021] [wsgi:error] [pid 27170:tid 2805986336] Exception in thread Track Loader Thread:
                [Sat Jul 31 17:26:02.678861 2021] [wsgi:error] [pid 27170:tid 2805986336] Traceback (most recent call last):
                [Sat Jul 31 17:26:02.678880 2021] [wsgi:error] [pid 27170:tid 2805986336]   File "/usr/lib/python3.7/threading.py", line 917, in _bootstrap_inner
                [Sat Jul 31 17:26:02.678899 2021] [wsgi:error] [pid 27170:tid 2805986336]     self.run()
                [Sat Jul 31 17:26:02.678936 2021] [wsgi:error] [pid 27170:tid 2805986336]   File "/usr/lib/python3.7/threading.py", line 865, in run
                [Sat Jul 31 17:26:02.678953 2021] [wsgi:error] [pid 27170:tid 2805986336]     self._target(*self._args, **self._kwargs)
                [Sat Jul 31 17:26:02.679009 2021] [wsgi:error] [pid 27170:tid 2805986336]   File "/data/django/jukeoroni/player/player.py", line 416, in _track_loader_task
                [Sat Jul 31 17:26:02.679028 2021] [wsgi:error] [pid 27170:tid 2805986336]     next_track = self.get_next_track()
                [Sat Jul 31 17:26:02.679045 2021] [wsgi:error] [pid 27170:tid 2805986336]   File "/data/django/jukeoroni/player/player.py", line 730, in get_next_track
                [Sat Jul 31 17:26:02.679061 2021] [wsgi:error] [pid 27170:tid 2805986336]     previous_track_id = self.playing_track.track.id
                [Sat Jul 31 17:26:02.679076 2021] [wsgi:error] [pid 27170:tid 2805986336] AttributeError: 'NoneType' object has no attribute 'track'
                """

                album = DjangoTrack.objects.get(id=previous_track_id).album_id
                album_tracks = DjangoTrack.objects.filter(album_id=album)
                next_track = album_tracks[0]

            return next_track

        return next_track

    def next(self):
        self.stop()

    def stop(self):
        self._playback_thread = None
        # TODO: maybe kill a specific process is more elegant
        os.system('killall ffplay')

    def set_image(self, **kwargs):
        thread = threading.Thread(target=self.task_pimoroni_set_image, kwargs=kwargs)
        thread.name = 'Set Image Thread'
        thread.daemon = False
        self._pimoroni_thread = thread


def player():
    p = Player(auto_update_tracklist=True)
    p.temp_cleanup()
    p.buttons_watcher_thread()
    p.state_watcher_thread()
    p.pimoroni_watcher_thread()
    p.set_image()
    p.track_list_generator_thread(auto_update_tracklist_interval=DEFAULT_TRACKLIST_REGEN_INTERVAL / 4)  # effect only if auto_update_tracklist=True
    p.track_loader_thread()


if __name__ == '__main__':
    player()

"""

Exception in thread Track Loader Thread:
Traceback (most recent call last):
  File "/usr/lib/python3.7/threading.py", line 917, in _bootstrap_inner
    self.run()
  File "/usr/lib/python3.7/threading.py", line 865, in run
    self._target(*self._args, **self._kwargs)
  File "/data/django/jukeoroni/player/player.py", line 338, in _track_loader_task
    next_track = self.get_next_track()
  File "/data/django/jukeoroni/player/player.py", line 711, in get_next_track
    previous_track_id = self.playing_track.track.id
AttributeError: 'NoneType' object has no attribute 'track'

waiting for loading thread to kick in

removed from local filesystem: "/tmp/tmpgc4kybmv"
"""


"""
source /data/venv/bin/activate
cd /data/django/jukeoroni/ && git pull && python manage.py shell

from player.player import Player
p = Player()
p.temp_cleanup()
p.buttons_watcher_thread()
p.state_watcher_thread()
p.pimoroni_watcher_thread()
p.track_loader_thread()
p.set_image()

"""