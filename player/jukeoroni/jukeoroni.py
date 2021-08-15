import random
import time
import threading
import subprocess
import logging
import signal
import RPi.GPIO as GPIO
from inky.inky_uc8159 import Inky  # , BLACK
from player.jukeoroni.displays import Standby as StandbyLayout
from player.jukeoroni.displays import Radio as RadioLayout
from player.models import Channel
# from player.displays import Player as PlayerLayout
# from player.jukeoroni.settings import BUTTONS
from player.jukeoroni.settings import PIMORONI_SATURATION, CLOCK_UPDATE_INTERVAL, OFF_IMAGE


LOG = logging.getLogger(__name__)


# CLOCK_UPDATE_INTERVAL = 1  # in minutes


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
BUTTON_X000_LABELS = 'Player'
BUTTON_0X00_LABELS = 'Radio'
BUTTON_00X0_LABELS = 'N//A'
BUTTON_000X_LABELS = 'N//A'


GPIO.setmode(GPIO.BCM)
GPIO.setup(_BUTTON_PINS, GPIO.IN, pull_up_down=GPIO.PUD_UP)


FFPLAY_CMD = 'ffplay -hide_banner -autoexit -vn -nodisp -loglevel error'.split(' ')


"""
django_shell

from player.jukeoroni.jukeoroni import JukeOroni
j = JukeOroni()
j.test = True
j.turn_on()

j.turn_off()
"""


class Radio(object):
    def __init__(self):
        # self.on = False
        self.is_on_air = False

        self.playback_proc = None

    @property
    def channels(self):
        return Channel.objects.all()

    @staticmethod
    def get_channels_by_kwargs(**kwargs):
        # self.get_channels_by_kwargs(display_name_short='srf_swiss_pop')[0])
        return Channel.objects.filter(**kwargs)

    @property
    def random_channel(self):
        return random.choice(self.channels)

    @property
    def last_played(self):
        return Channel.objects.get(last_played=True)


class JukeOroni(object):

    # PAUSE_RESUME_TOGGLE = {signal.SIGSTOP: signal.SIGCONT,
    #                        signal.SIGCONT: signal.SIGSTOP}

    def __init__(self):

        self.test = False

        self.on = False

        # self.jukebox = JukeBox()
        self.radio = Radio()

        self.playback_proc = None
        self.inserted_media = None

        self.button_X000_value = BUTTON_X000_LABELS
        self.button_0X00_value = BUTTON_0X00_LABELS
        self.button_00X0_value = BUTTON_00X0_LABELS
        self.button_000X_value = BUTTON_000X_LABELS

        self.pimoroni = Inky()

        self._current_time = None

        # display layouts
        self.layout_standby = StandbyLayout()
        self.layout_radio = RadioLayout()
        # self.layout_jukebox = PlayerLayout()

        self._pimoroni_thread_queue = None

        # Watcher threads
        self._pimoroni_watcher_thread = None
        # self._buttons_watcher_thread = None
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
    # playback workflow
    def insert(self, media):
        # j.insert(j.radio.last_played)
        assert isinstance(media, (Channel)), 'can only insert Channel model'
        self.inserted_media = media

    def play(self):
        assert self.playback_proc is None, 'there is an active playback. stop() first.'
        assert self.inserted_media is not None, 'no media inserted. insert media first.'

        if isinstance(self.inserted_media, Channel):
            self.radio.is_on_air = True
            self.playback_proc = subprocess.Popen(FFPLAY_CMD + [self.inserted_media.url], shell=False)

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

        self.radio.is_on_air = False
        self.playback_proc = None

    def next(self):
        raise NotImplementedError

    def previous(self):
        raise NotImplementedError

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
        self._start_jukeoroni()
        self._start_modules()

    def _start_jukeoroni(self):
        self.on = True
        self.set_image()
        # self.buttons_watcher_thread()
        self.state_watcher_thread()
        self.pimoroni_watcher_thread()

    def _start_modules(self):
        if not self.test:
            self.layout_standby.radar.start()
    ############################################

    ############################################
    # shutdown procedure
    def turn_off(self):

        self._stop_modules()

        self.pimoroni.set_image(OFF_IMAGE, saturation=PIMORONI_SATURATION)
        self.pimoroni.show(busy_wait=False)

    def _stop_jukeoroni(self):
        self.on = False

    def _stop_modules(self):
        if not self.test:
            print('terminating self.layout_standby.radar...')
            self.layout_standby.radar.stop()
            print('self.layout_standby.radar terminated')
    ############################################

    ############################################
    # pimoroni_watcher_thread
    # checks if display update is required
    # display has to be updated, we submit a thread
    # to self._pimoroni_thread_queue by calling set_image()
    def pimoroni_watcher_thread(self):
        self._pimoroni_watcher_thread = threading.Thread(target=self._pimoroni_watcher_task)
        self._pimoroni_watcher_thread.name = 'Pimoroni Watcher Thread'
        self._pimoroni_watcher_thread.daemon = False
        self._pimoroni_watcher_thread.start()

    def _pimoroni_watcher_task(self):
        update_interval = 5
        _waited = None
        while self.on:
            if _waited is None or _waited % update_interval == 0:
                _waited = 0
                if self._pimoroni_thread_queue is not None:
                    thread = self._pimoroni_thread_queue
                    self._pimoroni_thread_queue = None
                    # if not thread.is_alive():
                    thread.start()
                    # while thread.is_alive():
                    #     time.sleep(1.0)

            print(f'_pimoroni_watcher_task waited: {_waited}')
            time.sleep(1.0)
            _waited += 1

        print('terminating self._pimoroni_watcher_thread...')
        self._pimoroni_watcher_thread.join()
        self._pimoroni_watcher_thread = None
        print('self._pimoroni_watcher_thread terminated')

    def set_image(self, **kwargs):
        # TODO filter for types of images
        #  url, local path, Image.Image, Track
        thread = threading.Thread(target=self.task_pimoroni_set_image, kwargs=kwargs)
        thread.name = 'Set Image Thread'
        thread.daemon = False
        self._pimoroni_thread_queue = thread

    def task_pimoroni_set_image(self, **kwargs):
        # magic here...
        bg = self.layout_standby.get_layout(labels=self.LABELS)
        self.pimoroni.set_image(bg, saturation=PIMORONI_SATURATION)
        self.pimoroni.show(busy_wait=False)
    ############################################

    # ############################################
    # # buttons_watcher_thread
    # def buttons_watcher_thread(self):
    #     self._buttons_watcher_thread = threading.Thread(target=self._buttons_watcher_task)
    #     self._buttons_watcher_thread.name = 'Buttons Watcher Thread'
    #     self._buttons_watcher_thread.daemon = False
    #     self._buttons_watcher_thread.start()
    #
    # def _buttons_watcher_task(self):
    #     for pin in BUTTONS:
    #         GPIO.add_event_detect(pin, GPIO.FALLING, self._handle_button, bouncetime=250)
    #     signal.pause()
    #
    # def _handle_button(self, pin):
    #     button = BUTTONS.index(pin)
    #     logging.info(f"Button press detected on pin: {pin} button: {button}")
    #     print(f"Button press detected on pin: {pin} button: {button}")
    # ############################################

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
                self.set_image()

            print(f'_state_watcher_task waited: {_waited}')
            time.sleep(1.0)
            _waited += 1

        print('terminating self._state_watcher_thread...')
        self._state_watcher_thread.join()
        self._state_watcher_thread = None
        print('self._state_watcher_thread terminated')
    ############################################

    # def insert_media(self, media):
    #     pass
    #
    # def eject_media(self):
    #     pass


