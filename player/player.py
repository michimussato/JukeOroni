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
from .models import Track as DjangoTrack
from .models import Artist
from .models import Album


LOG = logging.getLogger(__name__)

MEDIA_ROOT = r'/data/googledrive/media/audio/'
CACHE_FILE = os.path.join(MEDIA_ROOT, 'music_cache_test.txt')
MISSING_COVERS_FILE = os.path.join(MEDIA_ROOT, 'missing_covers_test.txt')
FAULTY_ALBUMS = os.path.join(MEDIA_ROOT, 'faulty_albums_test.txt')
MUSIC_DIR = os.path.join(MEDIA_ROOT, 'music')
MAX_CACHED_FILES = 3
PIMORONI_SATURATION = 1.0
PIMORONI_SIZE = 600, 448
FONT_SIZE = 12
SLEEP_IMAGE = '/data/django/jukeoroni/player/static/zzz.jpg'
LOADING_IMAGE = '/data/django/jukeoroni/player/static/loading.jpg'
STANDARD_COVER = '/data/django/jukeoroni/player/static/cover_std.png'
PIMORONI_FONT = '/data/django/jukeoroni/player/static/arial_narrow.ttf'
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


class Track(object):
    def __init__(self, track, cached=True):
        self.track = track
        self.path = self.track.audio_source
        self.cached = cached
        self.cache = None

        if self.cached:
            self._cache()

    #@property
    #def track_list(self):
    #    return [track.audio_source for track in DjangoTrack.objects.all()]

    #@property
    #def media_index(self):
    #    return self.track_list.index(self.path)

    #@property
    #def album_indices(self):
    #    album_list = [i for i in self.track_list if os.path.dirname(self.path) in i]
    #    album_indices = []
    #    for i in album_list:
    #        if i in self.track_list:
    #            album_indices.append(self.track_list.index(i))#

    #    logging.info('{0} of albums found.'.format(album_indices))
    #    return album_indices

    @property
    def cover(self):
        album = Album.objects.get(track=self.track)
        return album.cover
        # cover_root = os.path.dirname(self.path)
        # jpg_path = os.path.join(cover_root, 'cover.jpg')
        # png_path = os.path.join(cover_root, 'cover.png')
        # if os.path.exists(jpg_path):
        #     img_path = jpg_path
        # elif os.path.exists(png_path):
        #     img_path = png_path
        # else:
        #     # TODO: put to file to fill in the covers later
        #     with open(MISSING_COVERS_FILE, 'a+') as f:
        #         f.write(cover_root + '\n')
        #     logging.info('cover is None')
        #     return None
        # logging.info('cover is \"{0}\"'.format(img_path))
        # return img_path

    @property
    def media_info(self):
        return mediainfo(self.path)

    def _cache(self):
        self.cache = tempfile.mkstemp()[1]
        logging.info('copying to local filesystem: \"{0}\" as \"{1}\"'.format(self.path, self.cache))
        shutil.copy(self.path, self.cache)

    @property
    def playing_from(self):
        return self.cache if self.cached else self.path

    def play(self):
        try:
            # ffplay -threads
            logging.info('starting playback: \"{0}\" from: \"{1}\"'.format(self.path, self.playing_from))
            self.track.played += 1
            self.track.save()
            os.system('ffplay -hide_banner -autoexit -vn -nodisp -loglevel error \"{0}\"'.format(self.playing_from))
            logging.info('playback finished: \"{0}\"'.format(self.path))
        except Exception:
            logging.exception('playback failed: \"{0}\"'.format(self.path))

    def __del__(self):
        if self.cache is not None:
            try:
                os.remove(self.cache)
                logging.info('removed from local filesystem: \"{0}\"'.format(self.cache))
            except Exception:
                logging.exception('deletion failed: \"{0}\"'.format(self.cache))
        else:
            pass


class Player(object):

    def __init__(self, auto_update_tracklist=False):
        logging.info('initializing player...')
        # assert state in LABELS, "state should be one of {0}".format(LABELS)
        self.button_1_value = BUTTON_1['Albm']
        self.button_2_value = BUTTON_2['Stop']
        self.button_3_value = BUTTON_3['Next']
        self.button_4_value = BUTTON_4['Quit']

        self.auto_update_tracklist = auto_update_tracklist
        self.tracks = []
        self.loading = 0
        self.playing = False
        self.playing_track = None
        self.sequential = False
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
                # # empty the cached tracks to create a new list based mode
                # # TODO: also remove from file system
                # self.tracks = []
                # self.button_1_value = BUTTON_1[current_label]
                # if self.button_1_value == 'Albm':
                #     self.next()
                # if self.button_1_value == 'Sequ':
                #     # has to update the buttons on the screen without self.next()
                #     self.set_image(image_file=self.playing_track.cover, media_info=self.playing_track.media_info)

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
            elif current_label == 'Next':
                self.next()

        # Quit button
        if current_label == self.button_4_value:
            return
            # self.init_screen()
            # self.quit()
    ############################################

    ############################################
    # track list generator
    def track_list_generator_thread(self, **kwargs):
        self._track_list_generator_thread = threading.Thread(target=self.track_list_generator_task, kwargs=kwargs)
        self._track_list_generator_thread.name = 'Track List Generator Thread'
        self._track_list_generator_thread.daemon = False
        self._track_list_generator_thread.start()

    def track_list_generator_task(self, **kwargs):
        while True and not self._quit:
            if self.auto_update_tracklist:

                self.create_update_track_list()

            time.sleep(kwargs.get('auto_update_tracklist_interval') or DEFAULT_TRACKLIST_REGEN_INTERVAL)  # is 12 hours

    @staticmethod
    def create_update_track_list():
        # TODO: filter image files, m3u etc.
        logging.info('generating updated track list...')
        _files = []
        for path, dirs, files in os.walk(MUSIC_DIR):
            print(path)
            # print(path)
            album = os.path.basename(path)
            print('  ' + album)
            try:
                artist, year, title = album.split(' - ')
                print('    ' + artist)
                print('    ' + year)
                print('    ' + title)
            except ValueError as err:
                with open(FAULTY_ALBUMS, 'a+') as f:
                    f.write(album + '\n')
                # TODO: store this somewhere to fix it
                LOG.exception('not a valid album path: {0}'.format(album))
                continue

            query_artist = Artist.objects.filter(name__exact=artist)
            if bool(query_artist):
                model_artist = query_artist[0]
                print('    artist found in db')
            else:
                model_artist = Artist(name=artist)
                model_artist.save()
                print('    artist created in db')

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
                logging.info('cover is None')
                img_path = None

            query_album = Album.objects.filter(album_title__exact=title, year__exact=year)

            if bool(query_album):
                model_album = query_album[0]
                model_album.cover = img_path
                print('    album found in db')
            else:
                model_album = Album(artist_id=model_artist, album_title=title, year=year, cover=img_path)
                print('    album created in db')

            try:
                model_album.save()
            except Exception:
                import pdb;pdb.set_trace()

            for _file in files:
                print('        file: ' + _file)
                if os.path.splitext(_file)[1] in AUDIO_FILES:
                    file_path = os.path.join(path, _file)
                    query_track = DjangoTrack.objects.filter(audio_source__exact=file_path)
                    if bool(query_track):
                        model_track = query_track[0]

                        print('      track found in db')
                    else:
                        model_track = DjangoTrack(album_id=model_album, audio_source=file_path)
                        model_track.save()
                        print('      track created in db')

                    _files.append(file_path)

        print(len(_files))

        # remove obsolete db objects:
        django_tracks = DjangoTrack.objects.all()
        for django_track in django_tracks:
            if django_track.audio_source not in _files:
                django_track.delete()

        logging.info('track list generated successfully: {0} tracks found'.format(len(files)))
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
                thread = threading.Thread(target=self._load_track_task, kwargs={'track': next_track})
                # TODO: maybe this name is not ideal
                thread.name = 'Track Loader Task Thread'
                thread.daemon = False
                self.loading += 1
                thread.start()
            time.sleep(1.0)

    def _load_track_task(self, **kwargs):
        track = kwargs['track']
        logging.debug('starting thread: \"{0}\"'.format(track.audio_source))

        try:
            #logging.error(track)
            #logging.error(track.audio_source)
            logging.info('loading track ({1} MB): \"{0}\"'.format(track.audio_source, str(round(os.path.getsize(track.audio_source) / (1024*1024), 3))))
            processing_track = Track(track)
            self.tracks.append(processing_track)
            logging.info('loading successful: \"{0}\"'.format(track.audio_source))
        except MemoryError as err:
            logging.exception('loading failed: \"{0}\"'.format(track.audio_source))
        finally:
            self.loading -= 1
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
                self.set_image(image_file=LOADING_IMAGE)
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
            # self.set_image(track.cover, track.media_info)
            self.set_image(track=track)

    def _playback_task(self, **kwargs):
        self.playing_track = kwargs['track']
        logging.debug('starting playback thread: for {0} from {0}'.format(self.playing_track.path, self.playing_track.playing_from))  # TODO add info
        self.playing_track.play()

        # cleanup
        self.playing_track = None
        self._playback_thread = None
    ############################################

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
            track = self.tracks.pop(0)
            del track

        sys.exit(0)

    def task_pimoroni_set_image(self, **kwargs):
        if 'track' in kwargs:
            cover = kwargs['track'].cover
        elif 'image_file' in kwargs:
            cover = kwargs['image_file']
        else:
            cover = STANDARD_COVER
        #else:
        #    cover = kwargs['image_file']


        if 'track' in kwargs:
            track = kwargs['track']
            title = os.path.basename(track.path)
            album = Album.objects.get(track=track.track)
            artist = Artist.objects.get(album=album)
            text = 'Track: {0}\nArtist: {1}\nAlbum: {2}'.format(
                title,
                artist,
                album
            )
        elif 'message' in kwargs:
            text = kwargs['message']
        #if bool(kwargs['media_info']):
        #    text = self.get_text(kwargs['media_info'])
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

        font_path = PIMORONI_FONT
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
        self.set_image(image_file=SLEEP_IMAGE)

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

    # def get_text(self, media_info):
    #     if 'TAG' in media_info:
    #         TAG = media_info['TAG']
    #         if 'ARTIST' in TAG:
    #             ARTIST = TAG['ARTIST']
    #         else:
    #             ARTIST = 'N/A'
    #
    #         if 'ALBUM' in TAG:
    #             ALBUM = TAG['ALBUM']
    #         else:
    #             ALBUM = 'N/A'
    #
    #         if 'TITLE' in TAG:
    #             TITLE = TAG['TITLE']
    #         else:
    #             TITLE = 'N/A'
    #
    #         if 'track' in TAG:
    #             track = TAG['track']
    #         else:
    #             track = 'N/A'
    #
    #         if 'channels' in media_info:
    #             channels = media_info['channels']
    #         else:
    #             channels = 'N/A'
    #
    #         if 'bits_per_raw_sample' in media_info:
    #             bits_per_raw_sample = media_info['bits_per_raw_sample']
    #         else:
    #             bits_per_raw_sample = 'N/A'
    #
    #         if 'sample_rate' in media_info:
    #             sample_rate = media_info['sample_rate']
    #         else:
    #             sample_rate = 'N/A'
    #
    #         if 'duration' in media_info:
    #             duration = time.gmtime(int(float(media_info['duration'])))
    #             duration = time.strftime("%H:%M:%S", duration)
    #
    #         else:
    #             duration = 'N/A'
    #
    #         ret = "Artist: {artist}\nAlbum: {album}\nTitle: {title} ({track})\nDuration: {duration}\n\nChannels: {channels}\nResolution: {bits_per_raw_sample} bits\nSample rate: {sample_rate} Hz".format(
    #             artist=ARTIST.upper(),
    #             album=ALBUM,
    #             track=track,
    #             title=TITLE,
    #             channels=channels,
    #             bits_per_raw_sample=bits_per_raw_sample,
    #             sample_rate=sample_rate,
    #             duration=duration)
    #
    #     else:
    #         ret = media_info['filename']
    #
    #     return ret

    @property
    def track_list(self):
        # return [track.audio_source for track in DjangoTrack.objects.all()]
        return DjangoTrack.objects.all()

    def get_next_track(self):
        if self.button_1_value == 'Rand':
            tracks = self.track_list
            #logging.error(tracks)
            if not bool(tracks):
                return None
            next_track = random.choice(tracks)

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
    p.init_screen()
    p.track_list_generator_thread(auto_update_tracklist_interval=DEFAULT_TRACKLIST_REGEN_INTERVAL / 4)  # effect only if auto_update_tracklist=True
    p.track_loader_thread()


if __name__ == '__main__':
    player()
