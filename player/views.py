from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect


import os
import sys
import glob
import random
import time
from pydub.utils import mediainfo
import threading
import logging
from inky.inky_uc8159 import Inky, CLEAN
import signal
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
import shutil
import tempfile


LOG = None

MEDIA_ROOT = r'/data/googledrive/media/audio/'
CACHE_FILE = os.path.join(MEDIA_ROOT, 'music_cache_test.txt')
MISSING_COVERS_FILE = os.path.join(MEDIA_ROOT, 'missing_covers_test.txt')
MUSIC_DIR = os.path.join(MEDIA_ROOT, 'music')
MAX_CACHED_FILES = 3
PIMORONI_SATURATION = 1.0
PIMORONI_SIZE = 600, 448
FONT_SIZE = 12
SLEEP_IMAGE = '/data/JukeOroni/zzz.jpg'
LOADING_IMAGE = '/data/JukeOroni/loading.jpg'
DEFAULT_TRACKLIST_REGEN_INTERVAL = 43200

# buttons setup
BUTTONS = [5, 6, 16, 24]
# BUTTONS = [24, 16, 6, 5]
# LABELS = ['Quit', 'Play', 'Next', 'Stop']

# Toggles:
# https://stackoverflow.com/questions/8381735/how-to-toggle-a-value
BUTTON_1 = {
            'Albm': 'Rand',
            'Rand': 'Sequ',
            'Sequ': 'Albm',
            }
BUTTON_2 = {
            'Stop': 'Stop',
            }
BUTTON_3 = {
            'Next': 'Play',
            'Play': 'Next'
            }
BUTTON_4 = {
            'Quit': 'Quit',
            # 'back': 'Back',
            }

# Button   4       3       2       1
# LABELS = ['Stop', 'Next', 'Play', 'Quit']

# for portrait orientation, the order is reversed
# LABELS = [BUTTON_4, BUTTON_3, BUTTON_2, BUTTON_1]

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# Audio files to index:
AUDIO_FILES = ['.dsf', '.flac', '.wav', '.dff']


# # https://medium.com/greedygame-engineering/an-elegant-way-to-run-periodic-tasks-in-python-61b7c477b679
# class Job(threading.Thread):
#     def __init__(self, interval, execute, *args, **kwargs):
#         threading.Thread.__init__(self)
#         self.daemon = False
#         self.stopped = threading.Event()
#         self.interval = interval
#         self.execute = execute
#         self.args = args
#         self.kwargs = kwargs

#     def stop(self):
#         self.stopped.set()
#         self.join()

#     def run(self):
#         while not self.stopped.wait(self.interval.total_seconds()):
#             self.execute(*self.args, **self.kwargs)


def init_logging(log_file=None, append=False, console_loglevel=logging.DEBUG):
    # """Set up logging to file and console."""
    # if log_file is not None:
    #     if append:
    #         filemode_val = 'a'
    #     else:
    #         filemode_val = 'w'
    #     logging.basicConfig(level=logging.DEBUG,
    #                         format="%(asctime)s %(levelname)s %(threadName)s %(thread)d %(name)s %(message)s",
    #                         # datefmt='%m-%d %H:%M',
    #                         filename=log_file,
    #                         filemode=filemode_val)
    # # define a Handler which writes INFO messages or higher to the sys.stderr
    # console = logging.StreamHandler()
    # console.setLevel(console_loglevel)
    # # set a format which is simpler for console use
    # formatter = logging.Formatter("%(message)s")
    # console.setFormatter(formatter)
    # # add the handler to the root logger
    # logging.getLogger('').addHandler(console)
    # global LOG
    # LOG = logging.getLogger(__name__)

    # https://docs.python.org/3.9/library/logging.html#logging.basicConfig
    #logging.basicConfig(level=logging.DEBUG,
    #                    format="[%(asctime)s] [%(levelname)s] [%(threadName)s|%(thread)d] [%(name)s]: %(message)s",
    #                    datefmt='%m-%d-%Y %H:%M:%S',
    #                    )
    global LOG
    LOG = logging.getLogger(__name__)


track_list = None


def get_track_list(txt=CACHE_FILE):
    global track_list
    if track_list is None:
        try:
            with open(txt, 'r') as f:
                logging.error('loading track list...')
                track_list = f.readlines()
                logging.error('track list loaded successfully: {0} tracks found'.format(len(track_list)))
                return [line.rstrip('\n') for line in track_list]
        except FileNotFoundError:
            # logging.exception(err)
            # print(err)
            logging.exception(
                'Mount Google Drive and try again. Use: \"rclone mount googledrive: /data/googledrive --vfs-cache-mode writes &\"')
    else:
        return track_list


class Track(object):
    def __init__(self, path, cached=True):
        self.path = path
        self.cached = cached
        self.cache = None

        if self.cached:
            self._cache()

    @property
    def track_list(self):
        return get_track_list(txt=CACHE_FILE)

    @property
    def media_index(self):
        return self.track_list.index(self.path)

    @property
    def album_indices(self):
        album_list = [i for i in self.track_list if os.path.dirname(self.path) in i]
        album_indices = []
        for i in album_list:
            if i in self.track_list:
                album_indices.append(self.track_list.index(i))

        logging.error('{0} of albums found.'.format(album_indices))
        return album_indices

    @property
    def cover(self):
        cover_root = os.path.dirname(self.path)
        jpg_path = os.path.join(cover_root, 'cover.jpg')
        png_path = os.path.join(cover_root, 'cover.png')
        if os.path.exists(jpg_path):
            img_path = jpg_path
        elif os.path.exists(png_path):
            img_path = png_path
        else:
            # TODO: put to file to fill in the covers later
            with open(MISSING_COVERS_FILE, 'a+') as f:
                f.write(cover_root + '\n')
            logging.error('cover is None')
            return None
        logging.error('cover is \"{0}\"'.format(img_path))
        return img_path

    @property
    def media_info(self):
        return mediainfo(self.path)

    def _cache(self):
        self.cache = tempfile.mkstemp()[1]
        logging.error('copying to local filesystem: \"{0}\" as \"{1}\"'.format(self.path, self.cache))
        shutil.copy(self.path, self.cache)

    @property
    def playing_from(self):
        return self.cache if self.cached else self.path

    def play(self):
        try:
            # ffplay -threads
            logging.error('starting playback: \"{0}\" from: \"{1}\"'.format(self.path, self.playing_from))
            os.system('ffplay -hide_banner -autoexit -vn -nodisp -loglevel error \"{0}\"'.format(self.playing_from))
            logging.error('playback finished: \"{0}\"'.format(self.path))
        except Exception:
            logging.exception('playback failed: \"{0}\"'.format(self.path))
            # logging.exception('ERROR:')

    def __del__(self):
        if self.cache is not None:
            try:
                os.remove(self.cache)
                logging.error('removed from local filesystem: \"{0}\"'.format(self.cache))
            except Exception:
                logging.exception('deletion failed: \"{0}\"'.format(self.cache))
        else:
            pass


"""

import time

from inky.inky_uc8159 import Inky, CLEAN


inky = Inky()

for _ in range(2):
    for y in range(inky.height - 1):
        for x in range(inky.width - 1):
            inky.set_pixel(x, y, CLEAN)

    inky.show()
    time.sleep(1.0)


>>> from inky.inky_uc8159 import Inky
>>> board = Inky()
from PIL import Image
saturation = 0.5
image = Image.open('image.img')
size = 600, 448
image_resized = image.resize(size, Image.ANTIALIAS)
board.set_image(image_resized, saturation=saturation)
board.show()

"""

"""
import signal
import RPi.GPIO as GPIO

print(buttons.py - Detect which button has been pressed

This example should demonstrate how to:
 1. set up RPi.GPIO to read buttons,
 2. determine which button has been pressed

Press Ctrl+C to exit!

)

# Gpio pins for each button (from top to bottom)
BUTTONS = [5, 6, 16, 24]

# These correspond to buttons A, B, C and D respectively
LABELS = ['A', 'B', 'C', 'D']

# Set up RPi.GPIO with the "BCM" numbering scheme
GPIO.setmode(GPIO.BCM)

# Buttons connect to ground when pressed, so we should set them up
# with a "PULL UP", which weakly pulls the input signal to 3.3V.
GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)


# "handle_button" will be called every time a button is pressed
# It receives one argument: the associated input pin.
def handle_button(pin):
    label = LABELS[BUTTONS.index(pin)]
    print("Button press detected on pin: {} label: {}".format(pin, label))


# Loop through out buttons and attach the "handle_button" function to each
# We're watching the "FALLING" edge (transition from 3.3V to Ground) and
# picking a generous bouncetime of 250ms to smooth out button presses.
for pin in BUTTONS:
    GPIO.add_event_detect(pin, GPIO.FALLING, handle_button, bouncetime=250)

# Finally, since button handlers don't require a "while True" loop,
# we pause the script to prevent it exiting immediately.
signal.pause()
"""


"""
DSF ffplay
ffplay -vn -nodisp '/data/googledrive/media/audio/music/on_device/The Prodigy - 2008 - Music For The Jilted Generation [DSD64]/Prodigy, The - Music For The Jilted Generation (2008, XLLP 114 - B668457, side 1)_2.8M.dsf'

DFF ffplay
ffplay -vn -nodisp '/data/googledrive/media/audio/music/new/Michael Jackson - 1982 - Thriller [DSD]/04 - Thriller.dff'

FLAC ffplay
ffplay -vn -nodisp '/data/googledrive/media/audio/music/on_device/Within Temptation - 2007 - The Heart Of Everything (Special Edition) [FLAC-24:192]/01 The Howling.flac'
"""


# def signal_handler(signum, frame):
#     raise ProgramKilled


class Player(object):

    """
from player.player import Player
p = Player()
p.buttons_watcher_thread()
p.state_watcher_thread()
p.pimoroni_watcher_thread()
p.init_screen()

p.track_list_generator_thread()
p.load_track_list()
p.track_loader_thread()

p.update_track_list()

# p.generate_track_list()
# p.buttons_watcher_thread()
# p.pimoroni_watcher_thread()
# p.state_watcher_thread()

# p.play()

# p.quit()
"""

    def __init__(self, auto_update_tracklist=False):
        logging.info('initializing player...')
        # assert state in LABELS, "state should be one of {0}".format(LABELS)
        self.button_1_value = BUTTON_1['Albm']
        self.button_2_value = BUTTON_2['Stop']
        self.button_3_value = BUTTON_3['Next']
        self.button_4_value = BUTTON_4['Quit']

        self.track_list = None
        self.auto_update_tracklist = auto_update_tracklist
        # self.played = []
        self.tracks = []
        self.loading = 0
        # self.track_list_album = None
        self.playing = False
        self.playing_track = None
        self.sequential = False
        # self.playing_now = None
        # self.media_info_now = None
        self._quit = False
        self.pimoroni = Inky()

        self._pimoroni_thread = None
        self._playback_thread = None
        self._buttons_watcher_thread = None
        self._track_loader_thread = None
        self._pimoroni_watcher_thread = None
        self._state_watcher_thread = None
        self._track_list_generator_thread = None

        logging.info('player initialized.')

    # @property
    # def playing_now_index(self):
    #     if self.playing_now is None and len(self.track) == 0:
    #         return self.track_list.index(random.choice(self.track_list))
    #     if self.button_1_value == 'Albm':
    #         return self.album_list.index(self.playing_now)
    #
    #     return self.track_list.index(self.playing_now)

    # @property
    # def album_list(self):
    #     return [i for i in self.track_list if os.path.dirname(self.playing_now) in i]

    def temp_cleanup(self):
        temp_dir = tempfile.gettempdir()
        logging.info('cleaning up {0}...'.format(temp_dir))
        for filename in glob.glob(os.path.join(temp_dir, 'tmp*')):
            os.remove(filename)
        logging.info('cleanup done.')

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
        logging.info("Button press detected on pin: {pin} label: {label}".format(pin=pin, label=current_label))

        # Mode button
        if self.button_3_value == 'Next':  # we only want to switch mode when something is already playing
            if current_label == self.button_1_value:
                return
                # empty the cached tracks to create a new list based mode
                # TODO: also remove from file system
                self.tracks = []
                self.button_1_value = BUTTON_1[current_label]
                if self.button_1_value == 'Albm':
                    self.next()
                if self.button_1_value == 'Sequ':
                    # has to update the buttons on the screen without self.next()
                    self.set_image(image_file=self.playing_track.cover, media_info=self.playing_track.media_info)

        # Stop button
        if current_label == self.button_2_value:
            if self._playback_thread is not None:
                self.button_3_value = BUTTON_3['Next']  # Switch button back to Play
                self.stop()
                self.init_screen()

        # Play/Next button
        if current_label == self.button_3_value:
            if current_label == 'Play':
                self.button_3_value = BUTTON_3[current_label]
                # self.play()
            elif current_label == 'Next':
                self.next()

        # Quit button
        if current_label == self.button_4_value:
            return
            self.init_screen()
            self.quit()

        # print('button layout is now\n\t{0}'.format('\n\t'.join(reversed(self.LABELS))))
    ############################################

    ############################################
    # track list generator
    # def update_track_list(self):
    #     # call this method to initiate track list creation/update
    #     # self.generate_new_track_list = True
    #     self.load_track_list()

    def track_list_generator_thread(self, **kwargs):
        self._track_list_generator_thread = threading.Thread(target=self.track_list_generator_task, kwargs=kwargs)
        self._track_list_generator_thread.name = 'Track List Generator Thread'
        self._track_list_generator_thread.daemon = False
        self._track_list_generator_thread.start()

    def track_list_generator_task(self, **kwargs):
        # self.load_track_list()
        while True and not self._quit:
            if self.auto_update_tracklist:
                # print('generating new track list...')

                self.generate_track_list()
                # print('track list generated.')

                # this is not a good approach to be able to quit directly, works for testing
                # is in separate thread already. maybe good enough.
                global track_list
                track_list = None

                self.load_track_list()

            time.sleep(kwargs.get('auto_update_tracklist_interval') or DEFAULT_TRACKLIST_REGEN_INTERVAL)  # is 12 hours

    def generate_track_list(self):
        # TODO: filter image files, m3u etc.
        logging.info('generating updated track list...')
        files = [
            os.path.join(path, filename)
            for path, dirs, files in os.walk(MUSIC_DIR)
            for filename in files
            if os.path.splitext(filename)[1] in AUDIO_FILES
        ]

        with open(CACHE_FILE, 'w') as f:
            for file in files:
                f.write(file + '\n')

        logging.info('track list generated successfully: {0} tracks found'.format(len(files)))
        # logging.info()

        # self.load_track_list()
        # self.generate_new_track_list = False
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
                thread = threading.Thread(target=self._load_track_task, kwargs={'path': next_track})
                # TODO: maybe this name is not ideal
                thread.name = 'Track Loader Task Thread'
                thread.daemon = False
                self.loading += 1
                thread.start()
            time.sleep(1.0)

    def _load_track_task(self, **kwargs):
        path = kwargs['path']
        logging.debug('starting thread: \"{0}\"'.format(path))
        # self.loading += 1

        try:
            # format_name = kwargs['media_info']['format_name']
            # print(kwargs['media_info'])
            # print('\n#############\nloading track:\n{0}'.format(path))
            # self.loading += 1
            logging.info('loading track ({1} MB): \"{0}\"'.format(path, str(round(os.path.getsize(path) / (1024*1024), 3))))
            processing_track = Track(path)
            # logging.debug('finished thread:\n\t{0}'.format(path))
            self.tracks.append(processing_track)
            logging.info('loading successful: \"{0}\"'.format(path))
        except MemoryError as err:
            logging.exception('loading failed: \"{0}\"'.format(path))
        finally:
            self.loading -= 1
            # print('-------------\nDone\n#############\n')

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
                    # print('PIMORONI IS WORKING.')
                    time.sleep(1.0)
            # print('NO PIMORONI JOB')
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
            if self.button_3_value == 'Next':  # Play
                # TODO implement Play/Next combo
                if self._playback_thread is None:
                    self.play()
                elif self._playback_thread.is_alive():
                    pass

            time.sleep(1.0)

        self.quit()
    ############################################

    ############################################
    # Playback
    def play(self):
        self.playback_thread()

    def playback_thread(self):
        while not self.tracks and not self.loading:
            print('waiting for loading thread to kick in   ', end='\r')
            time.sleep(0.2)
            print('waiting for loading thread to kick in.  ', end='\r')
            time.sleep(0.2)
            print('waiting for loading thread to kick in.. ', end='\r')
            time.sleep(0.2)
            print('waiting for loading thread to kick in...', end='\r')
            time.sleep(0.2)

        _display_loading = False
        while not self.tracks and self.loading:
            if not _display_loading:
                self.set_image(LOADING_IMAGE, '')
                _display_loading = True

            print('loading 1st track                       ', end='\r')
            time.sleep(0.2)
            print('loading 1st track.                      ', end='\r')
            time.sleep(0.2)
            print('loading 1st track..                     ', end='\r')
            time.sleep(0.2)
            print('loading 1st track...                    ', end='\r')
            time.sleep(0.2)

        del _display_loading

        if self.tracks:
            track = self.tracks.pop(0)

            self._playback_thread = threading.Thread(target=self._playback_task, kwargs={'track': track})
            self._playback_thread.name = 'Playback Thread'
            self._playback_thread.daemon = False
            self._playback_thread.start()

            # start playback first, then change image to prevent lag
            self.set_image(track.cover, track.media_info)

    def _playback_task(self, **kwargs):
        self.playing_track = kwargs['track']
        logging.debug('starting playback thread: for {0} from {0}'.format(self.playing_track.path, self.playing_track.playing_from))  # TODO add info
        # media_info = kwargs['media_info']
        # self.playing_now = self.playing_track.path
        # self.media_info_now = self.playing_track.media_info
        self.playing_track.play()

        # cleanup
        self.playing_track = None
        self._playback_thread = None
    ############################################

    def quit(self):
        self._quit = True
        # TODO: also remove from file system
        # # tracks = self.tracks
        # while self.tracks:
        #     track = self.tracks.pop(0)
        #     del track
        # # self.tracks = []

        self._track_list_generator_thread = None
        self._pimoroni_thread = None
        self._playback_thread = None
        self._buttons_watcher_thread = None
        self._track_loader_thread = None
        self._pimoroni_watcher_thread = None
        self._state_watcher_thread = None

        while self.tracks:
            track = self.tracks.pop(0)
            del track

        sys.exit(0)

    def task_pimoroni_set_image(self, **kwargs):
        if kwargs['image_file'] is None:
            cover = '/data/JukeOroni/cover_std.png'
        else:
            cover = kwargs['image_file']

        if bool(kwargs['media_info']):
            text = self.get_text(kwargs['media_info'])
        else:
            text = ''

        #image = Image.open(kwargs['image_file'])
        #image = image.rotate(90, expand=True)
        #image_resized = image.resize(self.PIMORONI_SIZE, Image.ANTIALIAS)
        #self.pimoroni.set_image(image_resized, saturation=self.PIMORONI_SATURATION)
        #self.pimoroni.show()

        bg = Image.new(mode='RGBA', size=(600, 448), color=(0, 0, 0, 255))
        # bg_w, bg_h = bg.size
        cover = Image.open(cover, 'r')
        w, h = cover.size
        if w == h:
            cover = cover.resize((448, 448), Image.ANTIALIAS)
        elif w > h:
            # TODO
            cover = cover.resize((448, 448), Image.ANTIALIAS)
        elif w < h:
            # TODO
            cover = cover.resize((448, 448), Image.ANTIALIAS)

        #offset = ((bg_w - w) // 2, (bg_h - h) // 2)
        #bg.paste(cover, offset)

        offset = (0, 0)

        #img_font = ImageFont.truetype('FreeMono.ttf', 20)
        
        #print(bg.size)
        #bg = bg.rotate(90, expand=False)
        #print(bg.size)

        #img_draw.text

        self.buttons_img_overlay(cover)

        # self.LABELS

        # buttons_img = Image.new(mode='RGB', size=(448, 12), color=(0, 0, 0))
        # buttons_draw = ImageDraw.Draw(buttons_img)
        # buttons_draw.text((0, 0), '       Quit               Play               Next               Stop', fill=(255, 255, 255))
        # # buttons_img = buttons_img.rotate(90, expand=False)
        # cover.paste(buttons_img, (0, 0))

        cover = cover.rotate(90, expand=True)
        # bg.paste(cover, offset)

        text_img = Image.new(mode='RGB', size=(448, 448), color=(0, 0, 0))
        img_draw = ImageDraw.Draw(text_img)

        font_path = "/data/JukeOroni/Arial Narrow.ttf"
        font = ImageFont.truetype(font_path, FONT_SIZE)
        #print(kwargs['media_info'])
        #img_draw.text((10, 5), self.wrap_text(kwargs['media_info']['filename']), fill=(255, 255, 255, 255))
        #img_draw.text((10, 5), self.get_text(kwargs['media_info']), fill=(255, 255, 255))
        img_draw.text((10, 0), text, fill=(255, 255, 255), font=font)

        text_img = text_img.rotate(90, expand=False)

        bg.paste(text_img, (448, 0))

        bg.paste(cover, offset)

        self.pimoroni.set_image(bg, saturation=PIMORONI_SATURATION)
        self.pimoroni.show()

    def init_screen(self):
        self.set_image(SLEEP_IMAGE, '')

    def buttons_img_overlay(self, bg):
        buttons_img = Image.new(mode='RGB', size=(448, 12), color=(0, 0, 0))
        buttons_draw = ImageDraw.Draw(buttons_img)
        buttons_draw.text((0, 0), '       {0}               {1}               {2}               {3}'.format(
            self.button_4_value,
            self.button_3_value,
            self.button_2_value,
            self.button_1_value,
        ), fill=(255, 255, 255))
        bg.paste(buttons_img, (0, 0))

    def get_text(self, media_info):
        if 'TAG' in media_info:
            TAG = media_info['TAG']
            if 'ARTIST' in TAG:
                ARTIST = TAG['ARTIST'] 
            else:
                ARTIST = 'N/A'

            if 'ALBUM' in TAG:
                ALBUM = TAG['ALBUM']
            else:
                ALBUM = 'N/A'

            if 'TITLE' in TAG:
                TITLE = TAG['TITLE']
            else:
                TITLE = 'N/A'

            if 'track' in TAG:
                track = TAG['track']
            else:
                track = 'N/A'

            if 'channels' in media_info:
                channels = media_info['channels']
            else:
                channels = 'N/A'

            if 'bits_per_raw_sample' in media_info:
                bits_per_raw_sample = media_info['bits_per_raw_sample']
            else:
                bits_per_raw_sample = 'N/A'

            if 'sample_rate' in media_info:
                sample_rate = media_info['sample_rate']
            else:
                sample_rate = 'N/A'

            if 'duration' in media_info:
                duration = time.gmtime(int(float(media_info['duration'])))
                duration = time.strftime("%H:%M:%S", duration)

            else:
                duration = 'N/A'

            ret = "Artist: {artist}\nAlbum: {album}\nTitle: {title} ({track})\nDuration: {duration}\n\nChannels: {channels}\nResolution: {bits_per_raw_sample} bits\nSample rate: {sample_rate} Hz".format(
                artist=ARTIST.upper(),
                album=ALBUM,
                track=track,
                title=TITLE,
                channels=channels,
                bits_per_raw_sample=bits_per_raw_sample,
                sample_rate=sample_rate,
                duration=duration)

        else:
            ret = media_info['filename']

        return ret

#     def task_pimoroni_clean(self):
#         """
# Exception in thread Thread-5:
# Traceback (most recent call last):
#   File "/usr/lib/python3.7/threading.py", line 917, in _bootstrap_inner
#     self.run()
#   File "/usr/lib/python3.7/threading.py", line 865, in run
#     self._target(*self._args, **self._kwargs)
#   File "/home/pi/player/player.py", line 250, in task_pimoroni_clean
#     self.pimoroni.set_pixel(x, y, CLEAN)
#   File "/home/pi/venv/lib/python3.7/site-packages/inky/inky_uc8159.py", line 343, in set_pixel
#     self.buf[y][x] = v & 0x07
# IndexError: index 448 is out of bounds for axis 0 with size 448
#         """
#         for _ in range(2):
#             for y in range(self.pimoroni.height - 1):
#                 for x in range(self.pimoroni.width - 1):
#                     self.pimoroni.set_pixel(x, y, CLEAN)
#             self.pimoroni.show()
#             time.sleep(1.0)

    # @property
    # def track_list(self):
    #     if self._reload_track_list:
    #         try:
    #             with open(self.CACHE_FILE, 'r') as f:
    #                 self.track_list = f.readlines()
    #         except FileNotFoundError as err:
    #             print(err)
    #             print('mount Google Drive and try again.\n\trclone mount googledrive: /data/googledrive &')

    def load_track_list(self, txt=CACHE_FILE):
        if os.path.exists(txt):
            self.track_list = get_track_list(txt)
        else:
            logging.info('CACHE_FILE does not exist yet.')

    def get_next_track(self):
        if self.button_1_value == 'Rand':
            if self.track_list is None:
                return None
            next_track = random.choice(self.track_list)

        elif self.button_1_value == 'Sequ':
            pass
            # # TODO: does not work if is loading and self.tracks is empty
            # # if not self.tracks and self.loading
            # print('track index: {0}'.format(self.playing_now_index))
            # print(len(self.tracks))
            # print(self.loading)
            # next_track = self.track_list[self.playing_now_index + len(self.tracks) + 1]  # + self.loading ?

        elif self.button_1_value == 'Albm':
            pass
            # next_track = self.album_list[self.playing_now_index + len(self.tracks)]  # play index 0 first, then up
            #
            # print(self.album_list)
            # # TODO: this will throw an error once the album is finished
            # #  will probably set self.button_1_value == 'Rand'
        # print('next track: {0}'.format(next_track))

        return next_track

    def next(self):
        self.stop()

    def stop(self):
        self._playback_thread = None
        # TODO: maybe kill a specific process is more elegant
        os.system('killall ffplay')

    # def get_cover(self, track_name):
    #     cover_root = os.path.dirname(track_name)
    #     jpg_path = os.path.join(cover_root, 'cover.jpg')
    #     png_path = os.path.join(cover_root, 'cover.png')
    #     if os.path.exists(jpg_path):
    #         img_path = jpg_path
    #     elif os.path.exists(png_path):
    #         img_path = png_path
    #     else:
    #         # TODO: put to file to fill in the covers later
    #         # print(cover_root)
    #         with open(MISSING_COVERS_FILE, 'a+') as f:
    #             f.write(cover_root + '\n')
    #         logging.debug('cover is None')
    #         return None
    #     logging.debug('cover is {0}'.format(img_path))
    #     return img_path

    def set_image(self, image_file, media_info):
        thread = threading.Thread(target=self.task_pimoroni_set_image, kwargs={'image_file': image_file, 'media_info': media_info})
        thread.name = 'Set Image Thread'
        thread.daemon = False
        self._pimoroni_thread = thread


"""
playing now: /data/googledrive/media/audio/music/new/Tool - Undertow - Custom Remaster by MC Lurken 24-bit 96kHz flac/Tracks 10-68 silence/32.flac
Exception in thread Thread-37:
Traceback (most recent call last):
  File "/usr/lib/python3.7/threading.py", line 917, in _bootstrap_inner
    self.run()
  File "/usr/lib/python3.7/threading.py", line 865, in run
    self._target(*self._args, **self._kwargs)
  File "/home/pi/player/player.py", line 121, in task_pimoroni_clean
    self.pimoroni.set_pixel(x, y, CLEAN)
  File "/home/pi/venv/lib/python3.7/site-packages/inky/inky_uc8159.py", line 343, in set_pixel
    self.buf[y][x] = v & 0x07
IndexError: index 448 is out of bounds for axis 0 with size 448
"""

p = Player(auto_update_tracklist=True)
p.temp_cleanup()
p.buttons_watcher_thread()
p.state_watcher_thread()
p.pimoroni_watcher_thread()
p.init_screen()
p.load_track_list()
p.track_list_generator_thread(auto_update_tracklist_interval=DEFAULT_TRACKLIST_REGEN_INTERVAL/4)  # effect only if auto_update_tracklist=True
p.track_loader_thread()


# Create your views here.
def index(request):
    return HttpResponse('Player page')
