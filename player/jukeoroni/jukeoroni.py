import time
import threading
import logging
import signal
import RPi.GPIO as GPIO
from inky.inky_uc8159 import Inky  # , BLACK
from player.displays import Standby as StandbyLayout
from player.displays import Player as PlayerLayout
from player.jukeoroni.settings import BUTTONS
from player.jukeoroni.settings import PIMORONI_SATURATION


LOG = logging.getLogger(__name__)


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


class JukeOroni(object):
    def __init__(self):
        # self.jukebox = JukeBox()
        # self.radio = Radio()

        self.button_X000_value = BUTTON_X000_LABELS
        self.button_0X00_value = BUTTON_0X00_LABELS
        self.button_00X0_value = BUTTON_00X0_LABELS
        self.button_000X_value = BUTTON_000X_LABELS

        self.pimoroni = Inky()

        # display layouts
        self.layout_standby = StandbyLayout()
        # self.layout_jukebox = PlayerLayout()
        # self.layout_radio = None

        self._pimoroni_thread_queue = None

        # Watcher threads
        self._pimoroni_watcher_thread = None
        self._buttons_watcher_thread = None
        self._state_watcher_thread = None

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
        # self.buttons_watcher_thread()
        self.pimoroni_watcher_thread()
        self.set_image()
    ############################################

    ############################################
    # shutdown procedure
    def turn_off(self):
        pass
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
        while True:
            if self._pimoroni_thread_queue is not None:
                thread = self._pimoroni_thread_queue
                self._pimoroni_thread_queue = None
                if not thread.is_alive():
                    thread.start()
                while thread.is_alive():
                    time.sleep(1.0)

            time.sleep(1.0)

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

    # ############################################
    # # State watcher (buttons)
    # # checks if the push of buttons or actions
    # # performed on web ui requires a state change
    # # TODO: define states
    # def state_watcher_thread(self):
    #     self._state_watcher_thread = threading.Thread(target=self.state_watcher_task)
    #     self._state_watcher_thread.name = 'State Watcher Thread'
    #     self._state_watcher_thread.daemon = False
    #     self._state_watcher_thread.start()
    #
    # def state_watcher_task(self):
    #     while True:
    #         # procedure goes in here
    #         time.sleep(1.0)
    # ############################################
