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


class JukeOroni(object):
    def __init__(self):
        # self.jukebox = JukeBox()
        # self.radio = Radio()

        self.pimoroni = Inky()

        # display layouts
        self.layout_standby = StandbyLayout()
        self.layout_jukebox = PlayerLayout()
        self.layout_radio = None

        self._pimoroni_thread_queue = None

        # Watcher threads
        self._pimoroni_watcher_thread = None
        self._buttons_watcher_thread = None
        self._state_watcher_thread = None

    ############################################
    # startup procedure
    def turn_on(self):
        self.buttons_watcher_thread()
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
        bg = kwargs
        self.pimoroni.set_image(bg, saturation=PIMORONI_SATURATION)
        self.pimoroni.show(busy_wait=False)
    ############################################

    ############################################
    # buttons_watcher_thread
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
        button = BUTTONS.index(pin)
        logging.info(f"Button press detected on pin: {pin} button: {button}")
        print(f"Button press detected on pin: {pin} button: {button}")
    ############################################

    ############################################
    # State watcher (buttons)
    # checks if the push of buttons or actions
    # performed on web ui requires a state change
    # TODO: define states
    def state_watcher_thread(self):
        self._state_watcher_thread = threading.Thread(target=self.state_watcher_task)
        self._state_watcher_thread.name = 'State Watcher Thread'
        self._state_watcher_thread.daemon = False
        self._state_watcher_thread.start()

    def state_watcher_task(self):
        while True:
            # procedure goes in here
            time.sleep(1.0)
    ############################################
