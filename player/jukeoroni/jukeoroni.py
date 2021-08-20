import random
import time
import io
import threading
import subprocess
import logging
import signal
import urllib.request
import urllib.error
from PIL import Image
import RPi.GPIO as GPIO
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from inky.inky_uc8159 import Inky  # , BLACK
from player.jukeoroni.displays import Off as OffLayout
from player.jukeoroni.displays import Standby as StandbyLayout
from player.jukeoroni.displays import Radio as RadioLayout
from player.models import Channel
from player.jukeoroni.settings import (
    PIMORONI_SATURATION,
    CLOCK_UPDATE_INTERVAL,
    OFF_IMAGE,
    PIMORONI_WATCHER_UPDATE_INTERVAL,
    GLOBAL_LOGGING_LEVEL,
    ON_AIR_DEFAULT_IMAGE,
    RADIO_ICON_IMAGE,
)


LOG = logging.getLogger(__name__)
LOG.setLevel(GLOBAL_LOGGING_LEVEL)


# buttons setup
# in portrait mode: from right to left
_BUTTON_PINS = [5, 6, 16, 24]
# highest index top, lowest index bottom
# (move items up and down for readability)
# also, the order here should be reflected
# in the order of the Player.LABELS property
# in order show up in the right order
BUTTON_STOP_BACK_PIN = _BUTTON_PINS[3]
BUTTON_PLAY_NEXT_PIN = _BUTTON_PINS[2]
BUTTON_RAND_ALBM_PIN = _BUTTON_PINS[1]
BUTTON_SHFL_SCRN_PIN = _BUTTON_PINS[0]

# # this will be the next layout:
# BUTTON_STOP_BACK_PIN = BUTTONS[3]
# BUTTON_PLAY_NEXT_PIN = BUTTONS[2]
# BUTTON_RAND_ALBM_PIN = BUTTONS[1]
# BUTTON_SHFL_SCRN_PIN = BUTTONS[0]


# Toggles:
# TODO: this is a brainfuck...have to think upside down
#  let's find a better way to toggle
# https://stackoverflow.com/questions/8381735/how-to-toggle-a-value
# # Standby
# BUTTON_X000_LABELS = 'Player'
# BUTTON_0X00_LABELS = 'Radio'
# BUTTON_00X0_LABELS = 'N//A'
# BUTTON_000X_LABELS = 'N//A'
# # Radio
# BUTTON_X000_LABELS = 'Back'
# BUTTON_0X00_LABELS = 'Play'
# BUTTON_00X0_LABELS = 'N//A'
# BUTTON_000X_LABELS = 'N//A'


FFPLAY_CMD = 'ffplay -hide_banner -autoexit -vn -nodisp -loglevel error'.split(' ')


def is_string_an_url(url_string: str) -> bool:
    validate_url = URLValidator()
    try:
        validate_url(url_string)
    except ValidationError:
        return False
    return True


class Radio(object):
    def __init__(self):
        self.is_on_air = None

        self.playback_proc = None

    @property
    def cover(self):
        cover = None
        if isinstance(self.is_on_air, Channel):
            cover = self.is_on_air.url_logo
            if cover is None:
                cover = ON_AIR_DEFAULT_IMAGE
            elif is_string_an_url(cover):
                try:
                    hdr = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}
                    req = urllib.request.Request(cover, headers=hdr)
                    response = urllib.request.urlopen(req)
                    if response.status == 200:
                        cover = io.BytesIO(response.read())
                        cover = Image.open(cover)
                except Exception as err:
                    LOG.exception(f'Could not get online cover:')
                    cover = ON_AIR_DEFAULT_IMAGE

            else:
                cover = Image.open(cover).resize((448, 448))
        elif self.is_on_air is None:
            cover = RADIO_ICON_IMAGE

        if cover is None:
            raise TypeError('Channel cover is None')

        return cover

    @property
    def button_X000_value(self):
        if self.is_on_air:
            return 'Stop'
        elif not self.is_on_air:
            return 'Back'

    @property
    def button_0X00_value(self):
        if self.is_on_air:
            return 'Next'
        elif not self.is_on_air:
            return 'Play'

    @property
    def button_00X0_value(self):
        if self.is_on_air:
            return '00X0'
        elif not self.is_on_air:
            return '00X0'

    @property
    def button_000X_value(self):
        if self.is_on_air:
            return '000X'
        elif not self.is_on_air:
            return '000X'

    @property
    def channels(self):
        return Channel.objects.all()

    @staticmethod
    def get_channels_by_kwargs(**kwargs):
        # i.e. self.get_channels_by_kwargs(display_name_short='srf_swiss_pop')[0])
        return Channel.objects.filter(**kwargs)

    @property
    def random_channel(self):
        return random.choice(self.channels)

    @property
    def last_played(self):
        return Channel.objects.get(last_played=True)


class JukeOroni(object):
    """
Django shell usage:

django_shell

from player.jukeoroni.jukeoroni import JukeOroni
j = JukeOroni()
# j.test = True
j.turn_on()

j.insert(j.radio.random_channel)
j.play()
j.change_media(j.radio.random_channel)
j.stop()
j.eject()

j.turn_off()
    """

    # PAUSE_RESUME_TOGGLE = {signal.SIGSTOP: signal.SIGCONT,
    #                        signal.SIGCONT: signal.SIGSTOP}

    def __init__(self):

        LOG.info(f'Initializing JukeOroni...')
        # TODO rename to headless
        self.test = False
        LOG.info(f'Test mode JukeOroni: {str("ON" if self.test else "OFF")}.')

        self.on = False

        # self.jukebox = JukeBox()
        self.radio = Radio()

        self.playback_proc = None
        self.inserted_media = None

        self.button_X000_value = None
        self.button_0X00_value = None
        self.button_00X0_value = None
        self.button_000X_value = None

        self.pimoroni = Inky()

        self._current_time = None

        # display layouts
        self.layout_off = OffLayout()
        self.layout_standby = StandbyLayout()
        self.layout_radio = RadioLayout()
        # self.layout_jukebox = PlayerLayout()

        self._pimoroni_thread_queue = None

        # Watcher threads
        self._pimoroni_watcher_thread = None
        self._buttons_watcher_thread = None
        self._state_watcher_thread = None

    def __str__(self):
        ret = 'JukeOroni\n'
        ret += f'\tis on: {str(self.on)}\n'
        ret += f'\tinserted_media: {str(self.inserted_media)}\n'
        ret += f'\tradio is on air: {str(self.radio.is_on_air)}\n'
        ret += f'\tplayback_proc is: {str(self.playback_proc)}\n'
        return ret

    def __del__(self):
        if self.radio.is_on_air:
            self.stop()
            self.eject()
            raise Exception('stop playback before exitting')
        if self.inserted_media is not None:
            self.eject()
            raise Exception('eject media before exitting')

    ############################################
    # set modes

    def set_mode_standby(self):
        self.set_display_standby()

    def set_mode_radio(self):
        self.set_display_radio()

    def set_mode_player(self):
        raise NotImplementedError
    ############################################

    ############################################
    # display background handling
    def pimoroni_init(self):
        self.pimoroni.__init__()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(_BUTTON_PINS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def set_display_standby(self):
        """
        j.set_display_standard()
        """
        self.set_display_turn_on()

    def set_display_turn_on(self):
        """
        j.set_display_turn_on()
        """
        assert self.on, 'turn_on first.'
        if not self.test:
            self.button_X000_value = 'Player'
            self.button_0X00_value = 'Radio'
            self.button_00X0_value = 'N//A'
            self.button_000X_value = 'N//A'
            self.set_image()
        else:
            LOG.info(f'Not setting TURN_ON image. Test mode.')

    def set_display_turn_off(self):
        """
        j.set_display_turn_off()
        """
        assert not self.on, 'JukeOroni needs to be turned off first.'
        if not self.test:
            self.button_X000_value = 'On'
            self.button_0X00_value = 'N//A'
            self.button_00X0_value = 'N//A'
            self.button_000X_value = 'N//A'
            self.pimoroni_init()
            LOG.info(f'Setting OFF Layout...')

            bg = self.layout_off.get_layout(labels=self.LABELS, cover=OFF_IMAGE)
            # self.set_image(image=bg)

            self.pimoroni.set_image(bg, saturation=PIMORONI_SATURATION)
            self.pimoroni.show(busy_wait=True)
            LOG.info(f'Done.')
        else:
            LOG.info(f'Not setting OFF_IMAGE. Test mode.')
        GPIO.cleanup()

    def set_display_radio(self):
        """
        j.set_display_radio()
        """
        if not self.test:
            self.button_X000_value = self.radio.button_X000_value
            self.button_0X00_value = self.radio.button_0X00_value
            self.button_00X0_value = self.radio.button_00X0_value
            self.button_000X_value = self.radio.button_000X_value

            bg = self.layout_radio.get_layout(labels=self.LABELS, cover=self.radio.cover)
            self.set_image(image=bg)
    ############################################

    ############################################
    # playback workflow
    def insert(self, media):
        # j.insert(j.radio.last_played)
        assert self.on, 'JukeOroni is OFF. turn_on() first.'
        assert self.inserted_media is None, 'There is a medium inserted already'
        # TODO: add types to tuple
        assert isinstance(media, (Channel)), 'can only insert Channel model'

        self.inserted_media = media
        LOG.info(f'Media inserted: {str(media)} (type {str(type(media))})')

        if isinstance(media, Channel):
            self.set_mode_radio()

    def play(self):
        assert self.playback_proc is None, 'there is an active playback. stop() first.'
        assert self.inserted_media is not None, 'no media inserted. insert media first.'

        if isinstance(self.inserted_media, Channel):
            hdr = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}
            req = urllib.request.Request(self.inserted_media.url, headers=hdr)
            try:
                # test if url is reachable
                response = urllib.request.urlopen(req)
            except urllib.error.HTTPError as err:
                bad_channel = self.inserted_media
                LOG.exception(f'Could not open URL: {str(bad_channel)}')
                raise

            if response.status == 200:
                self.radio.is_on_air = self.inserted_media
                self.playback_proc = subprocess.Popen(FFPLAY_CMD + [self.inserted_media.url], shell=False)
                try:
                    self.playback_proc.communicate(timeout=2.0)
                except subprocess.TimeoutExpired:
                    # this is the expected behaviour!!
                    LOG.info(f'ffplay started successfully. playing {str(self.inserted_media.display_name)}')
                    self.set_display_radio()
                else:
                    bad_channel = self.inserted_media
                    self.stop()
                    self.eject()
                    LOG.error(f'ffplay aborted inexpectedly, media ejected. Channel is not functional: {str(bad_channel)}')
                    raise Exception(f'ffplay aborted inexpectedly, media ejected. Channels is not functional: {str(bad_channel)}')
            else:
                LOG.error(f'Channel stream return code is not 200: {str(response.status)}')
                raise Exception(f'Channel stream return code is not 200: {str(response.status)}')

    def pause(self):
        assert self.inserted_media is not None, 'no media inserted. insert media first.'
        assert self.playback_proc is not None, 'no playback is active. play() media first'
        assert self.playback_proc.poll() is None, 'playback_proc was terminated. start playback first'
        self.playback_proc.send_signal(signal.SIGSTOP)

    def resume(self):
        assert self.inserted_media is not None, 'no media inserted. insert media first.'
        assert self.playback_proc is not None, 'no playback is active. play() media first'
        assert self.playback_proc.poll() is None, 'playback_proc was terminated. start playback first'
        self.playback_proc.send_signal(signal.SIGCONT)

    def stop(self):
        assert isinstance(self.playback_proc, subprocess.Popen), 'nothing is playing'

        self.playback_proc.terminate()

        while self.playback_proc.poll() is None:
            time.sleep(0.1)

        if isinstance(self.inserted_media, Channel):
            self.radio.is_on_air = None
            self.set_display_radio()

        self.playback_proc = None

    def next(self):
        raise NotImplementedError

    def previous(self):
        raise NotImplementedError

    def change_media(self, media):
        # convenience method
        _on_air = self.radio.is_on_air
        if self.radio.is_on_air:
            self.stop()
        self.eject()
        self.insert(media)
        if _on_air:
            self.play()

    def eject(self):
        assert self.inserted_media is not None, 'no media inserted. insert media first.'
        assert self.playback_proc is None, 'cannot eject media while playback is active. stop() first.'
        self.inserted_media = None
    ############################################

    @property
    def LABELS(self):
        # this will be sent to the display module
        # _BUTTONS is from right to left, but this
        # one should correspond to the the indexes
        # assigned to each button label: highest
        # index left, lowest index right
        # and here: top will be left on the screen,
        # bottom will be right on the screen
        return [
                   self.button_X000_value,
                   self.button_0X00_value,
                   self.button_00X0_value,
                   self.button_000X_value,
               ][::-1]  # reversed for readabilty (from left to right)

    ############################################
    # startup procedure
    def turn_on(self):
        assert not self.on, 'JukeOroni is ON already'
        self._start_jukeoroni()
        self._start_modules()

    def _start_jukeoroni(self):
        self.on = True

        self.pimoroni_init()

        self.buttons_watcher_thread()
        self.pimoroni_watcher_thread()
        self.state_watcher_thread()

        self.set_display_turn_on()

    def _start_modules(self):
        self.layout_standby.radar.start(test=self.test)
    ############################################

    ############################################
    # shutdown procedure
    def turn_off(self):
        assert self.on, 'JukeOroni is OFF already'
        assert self.playback_proc is None, 'there is an active playback. stop() first.'
        assert self.inserted_media is None, 'media inserted. eject() first.'

        self._stop_jukeoroni()
        self._stop_modules()

        # TODO: will be replaced with
        #  layout (self.task_pimoroni_set_image)
        #  as soon as we have a layout for this
        self.set_display_turn_off()

    def _stop_jukeoroni(self):
        self.on = False

        # cannot join() the threads from
        # within the threads themselves
        LOG.info(f'Terminating self._pimoroni_watcher_thread...')
        self._pimoroni_watcher_thread.join()
        self._pimoroni_watcher_thread = None
        LOG.info(f'self._pimoroni_watcher_thread terminated')

        LOG.info(f'Terminating self._state_watcher_thread...')
        self._state_watcher_thread.join()
        self._state_watcher_thread = None
        LOG.info(f'self._state_watcher_thread terminated')

        try:
            LOG.info(f'Terminating self._buttons_watcher_thread...')
            if self._buttons_watcher_thread.is_alive():
                thread_id = self._buttons_watcher_thread.ident
                signal.pthread_kill(thread_id, signal.SIGINT.value)
                self._buttons_watcher_thread.join()
        except KeyboardInterrupt:
            LOG.info(f'_buttons_watcher_thread killed by signal.SIGINT:')
        finally:
            self._buttons_watcher_thread = None
            LOG.info(f'self._buttons_watcher_thread terminated')

    def _stop_modules(self):
        LOG.info(f'Terminating self.layout_standby.radar...')
        self.layout_standby.radar.stop()
        LOG.info(f'self.layout_standby.radar terminated')
    ############################################

    ############################################
    # pimoroni_watcher_thread
    # checks if display update is required.
    # if display has to be updated, we submit a thread
    # to self._pimoroni_thread_queue by calling set_image()
    def pimoroni_watcher_thread(self):
        self._pimoroni_watcher_thread = threading.Thread(target=self._pimoroni_watcher_task)
        self._pimoroni_watcher_thread.name = 'Pimoroni Watcher Thread'
        self._pimoroni_watcher_thread.daemon = False
        self._pimoroni_watcher_thread.start()

    def _pimoroni_watcher_task(self):
        _waited = None
        while self.on:
            if _waited is None or _waited % PIMORONI_WATCHER_UPDATE_INTERVAL == 0:
                _waited = 0
                if self._pimoroni_thread_queue is not None:
                    thread = self._pimoroni_thread_queue
                    self._pimoroni_thread_queue = None
                    thread.start()

            time.sleep(1.0)
            _waited += 1

    def set_image(self, **kwargs):
        # TODO filter for types of images
        #  url, local path, Image.Image, Track
        thread = threading.Thread(target=self.task_pimoroni_set_image, kwargs=kwargs)
        thread.name = 'Set Image Thread'
        thread.daemon = False
        self._pimoroni_thread_queue = thread

    def task_pimoroni_set_image(self, **kwargs):
        if self.test:
            LOG.info(f'No Pimoroni update in test mode')
        else:
            LOG.info(f'Setting Pimoroni image...')
            if 'image' in kwargs:
                bg = kwargs['image']
            else:
                bg = self.layout_standby.get_layout(labels=self.LABELS)
            self.pimoroni.set_image(image=bg, saturation=PIMORONI_SATURATION)
            self.pimoroni.show(busy_wait=True)
            LOG.info(f'Done.')
    ############################################

    ############################################
    # buttons_watcher_thread
    def buttons_watcher_thread(self):
        self._buttons_watcher_thread = threading.Thread(target=self._buttons_watcher_task)
        self._buttons_watcher_thread.name = 'Buttons Watcher Thread'
        self._buttons_watcher_thread.daemon = False
        self._buttons_watcher_thread.start()

    def _buttons_watcher_task(self):
        for pin in _BUTTON_PINS:
            GPIO.add_event_detect(pin, GPIO.FALLING, self._handle_button, bouncetime=250)
        signal.pause()

    def _handle_button(self, pin):
        button = _BUTTON_PINS.index(pin)
        LOG.info(f'Button press detected on pin: {pin} button: {button}')
    ############################################

    ############################################
    # State watcher (buttons)
    # checks if the push of buttons or actions
    # performed on web ui requires a state change
    # TODO: define states
    def state_watcher_thread(self):
        self._state_watcher_thread = threading.Thread(target=self._state_watcher_task)
        self._state_watcher_thread.name = 'State Watcher Thread'
        self._state_watcher_thread.daemon = False
        self._state_watcher_thread.start()

    def _state_watcher_task(self):
        update_interval = CLOCK_UPDATE_INTERVAL*60
        _waited = None
        while self.on:
            if _waited is None or _waited % update_interval == 0:
                _waited = 0

            time.sleep(1.0)
            _waited += 1
    ############################################
