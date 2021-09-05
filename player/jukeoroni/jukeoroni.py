import os
import time
import threading
# import multiprocessing
import subprocess
import logging
import signal
import urllib.request
import urllib.error
import RPi.GPIO as GPIO
from django.utils.timezone import localtime, now
from inky.inky_uc8159 import Inky  # , BLACK
from player.jukeoroni.juke_radio import Radio
from player.jukeoroni.juke_box import Jukebox as Box
from player.jukeoroni.displays import Off as OffLayout
from player.jukeoroni.displays import Standby as StandbyLayout
from player.models import Channel
from player.jukeoroni.juke_box import JukeboxTrack
from player.jukeoroni.settings import (
    PIMORONI_SATURATION,
    # CLOCK_UPDATE_INTERVAL,
    PIMORONI_WATCHER_UPDATE_INTERVAL,
    GLOBAL_LOGGING_LEVEL,
    MODES,
    FFPLAY_CMD,
)
from player.jukeoroni.images import Resource


LOG = logging.getLogger(__name__)
LOG.setLevel(GLOBAL_LOGGING_LEVEL)


# buttons setup
# in portrait mode: from right to left
_BUTTON_PINS = [5, 6, 16, 24]
_BUTTON_MAPPINGS = ['000X', '00X0', '0X00', 'X000']
# highest index top, lowest index bottom
# (move items up and down for readability)
# also, the order here should be reflected
# in the order of the Player.LABELS property
# in order show up in the right order
# BUTTON_STOP_BACK_PIN = _BUTTON_PINS[3]
# BUTTON_PLAY_NEXT_PIN = _BUTTON_PINS[2]
# BUTTON_RAND_ALBM_PIN = _BUTTON_PINS[1]
# BUTTON_SHFL_SCRN_PIN = _BUTTON_PINS[0]

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


# FFPLAY_CMD = 'ffplay -hide_banner -autoexit -vn -nodisp -loglevel error'.split(' ')


class JukeOroni(object):
    """
Django shell usage:

django_shell

from player.jukeoroni.jukeoroni import JukeOroni
j = JukeOroni()
j.test = True
j.turn_on()

# RADIO
j.set_mode_radio()

# j.insert(j.radio.random_channel)
# j.jukebox_playback_thread()
j.insert(j.radio.last_played)
j.play()



# j.change_media(j.radio.random_channel)
# j.next(j.radio.get_channels_by_kwargs(display_name_short='bob-metal')[0])
j.next()
j.stop()
j.eject()

# JUKEBOX
j.jukebox.set_auto_update_tracklist_off()

# play:
j.set_mode_jukebox()

# j.insert(j.jukebox.next_track)
j.play()
j.stop()
j.next()


we want:
insert()
play()
next()
stop()
etc.


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
        self.mode = None
        self.set_mode_off()

        self.jukebox = Box(jukeoroni=self)
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
        self.layout_radio = self.radio.layout
        # self.layout_jukebox = PlayerLayout()

        self._pimoroni_thread_queue = None

        # Watcher threads
        self._pimoroni_watcher_thread = None
        self._buttons_watcher_thread = None
        self._state_watcher_thread = None

        self._jukebox_playback_thread = None
        self._playback_thread = None

        # self.set_display_turn_off()

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
    def set_mode_off(self):
        self.mode = MODES['jukeoroni']['off']

    def set_mode_standby(self):
        self.mode = MODES['jukeoroni']['standby']
        self.set_display_standby()

    def set_mode_radio(self):
        if self.radio.is_on_air:
            self.mode = MODES['radio']['on_air']
        elif not self.radio.is_on_air:
            self.mode = MODES['radio']['standby']
        self.set_display_radio()

    def set_mode_jukebox(self):
        if self.playback_proc is not None:
            self.mode = MODES['jukebox']['on_air'][self.jukebox.loader_mode]
        elif self.playback_proc is None:
            self.mode = MODES['jukebox']['standby'][self.jukebox.loader_mode]
        # wait because inserted_media can be none
        # while playback_proc is not fully terminated
        # maybe just a temp hack
        time.sleep(1.0)
        self.set_display_jukebox()

        # if self._jukebox_playback_thread is None:
        #     self.jukebox_playback_thread()
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
            self.button_X000_value = self.mode['buttons']['X000']
            self.button_0X00_value = self.mode['buttons']['0X00']
            self.button_00X0_value = self.mode['buttons']['00X0']
            self.button_000X_value = self.mode['buttons']['000X']
            self.set_image()
        else:
            LOG.info(f'Not setting TURN_ON image. Test mode.')

    def set_display_turn_off(self):
        """
        j.set_display_turn_off()
        """
        assert not self.on, 'JukeOroni needs to be turned off first.'
        if not self.test:
            self.button_X000_value = self.mode['buttons']['X000']
            self.button_0X00_value = self.mode['buttons']['0X00']
            self.button_00X0_value = self.mode['buttons']['00X0']
            self.button_000X_value = self.mode['buttons']['000X']
            self.pimoroni_init()
            LOG.info(f'Setting OFF Layout...')

            bg = self.layout_off.get_layout(labels=self.LABELS, cover=Resource().OFF_IMAGE_SQUARE)
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
            self.button_X000_value = self.mode['buttons']['X000']
            self.button_0X00_value = self.mode['buttons']['0X00']
            self.button_00X0_value = self.mode['buttons']['00X0']
            self.button_000X_value = self.mode['buttons']['000X']

            bg = self.radio.layout.get_layout(labels=self.LABELS, cover=self.radio.cover)
            self.set_image(image=bg)

    def set_display_jukebox(self):
        """
        j.set_display_jukebox()
        """
        if not self.test:
            self.button_X000_value = self.mode['buttons']['X000']
            self.button_0X00_value = self.mode['buttons']['0X00']
            self.button_00X0_value = self.mode['buttons']['00X0']
            self.button_000X_value = self.mode['buttons']['000X']

            if self.inserted_media is None and \
                    self.mode == MODES['jukebox']['standby'][self.jukebox.loader_mode]:
                bg = self.jukebox.layout.get_layout(labels=self.LABELS)
            elif self.inserted_media is None and \
                    self.mode == MODES['jukebox']['on_air'][self.jukebox.loader_mode]:
                bg = self.jukebox.layout.get_layout(labels=self.LABELS, loading=True)
            else:
                bg = self.jukebox.layout.get_layout(labels=self.LABELS, cover=self.inserted_media.cover_album, artist=self.inserted_media.cover_artist)
            self.set_image(image=bg)
    ############################################

    def state_watcher_thread(self):
        self._state_watcher_thread = threading.Thread(target=self.state_watcher_task)
        self._state_watcher_thread.name = 'State Watcher Thread'
        self._state_watcher_thread.daemon = False
        self._state_watcher_thread.start()

    def state_watcher_task(self):
        # assert self.jukebox.on, 'turn on jukebox before initiating state_watcher_task'
        while True:

            # new_time = localtime(now())

            _msg_printed = False
            # _loading = False
            while not self.jukebox.tracks and self.inserted_media is None:
                if not _msg_printed:
                    LOG.info('waiting for a jukebox track...')
                    # if self.mode == MODES['jukebox']['standby'] \
                    #         or self.mode == MODES['jukebox']['on_air']:
                    #     self.set_display_jukebox()

                    _msg_printed = True

                time.sleep(1.0)
            if _msg_printed:
                LOG.info('jukebox track loaded.')
                _msg_printed = False

            if self.mode == MODES['jukebox']['standby']['random'] \
                    or self.mode == MODES['jukebox']['standby']['album'] \
                    or self.mode == MODES['jukebox']['on_air']['random'] \
                    or self.mode == MODES['jukebox']['on_air']['album']:
                if self.inserted_media is None:
                    self.insert(self.jukebox.next_track)

            else:
                if isinstance(self.inserted_media, JukeboxTrack):
                    self.eject()

            if self.mode == MODES['jukebox']['standby']['random'] \
                    or self.mode == MODES['jukebox']['standby']['album']:
                pass

            elif self.mode == MODES['jukebox']['on_air']['random'] \
                    or self.mode == MODES['jukebox']['on_air']['album']:

                # TODO implement Play/Next combo
                if self.playback_proc is None:
                    self.jukebox_playback_thread()
                elif self.playback_proc is not None:
                    if self.playback_proc.poll() == 0:
                        # process finished. join()?
                        self.playback_proc = None
                    elif self.playback_proc.poll() is None:
                        # still playing
                        pass
                # elif self.playback_proc.poll() == 0:
                #     self.playback_proc = None
                # else:

            # elif self.current_time != new_time.strftime('%H:%M'):  # in stopped state
            #     if self.current_time is None or (int(new_time.strftime('%H:%M')[-2:])) % CLOCK_UPDATE_INTERVAL == 0:
            #         self.set_image()
            #         self.current_time = new_time.strftime('%H:%M')

            time.sleep(1.0)

    def jukebox_playback_thread(self):
        assert isinstance(self.inserted_media, JukeboxTrack)

        self._playback_thread = threading.Thread(target=self._playback_task)
        self._playback_thread.name = 'Playback Thread'
        self._playback_thread.daemon = False
        self._playback_thread.start()

    def _playback_task(self):
        LOG.info(f'starting playback thread: for {self.inserted_media.path} from {self.inserted_media.playing_from}')  # TODO add info
        # self.jukebox.playing_track = self.inserted_media
        self.inserted_media.play(jukeoroni=self)
        LOG.info('playback finished')
        # self.stop()
        self.eject()
        self._playback_thread = None
        self._jukebox_playback_thread = None
        self.playback_proc = None

        # cleanup
        # self._playback_thread.close()
        # self.playing_track = None
        # self._playback_thread = None
    ############################################

    ############################################
    # playback workflow
    def insert(self, media):
        # j.insert(j.radio.last_played)
        assert self.on, 'JukeOroni is OFF. turn_on() first.'
        assert self.inserted_media is None, 'There is a medium inserted already'
        # TODO: add types to tuple
        assert isinstance(media, (Channel, JukeboxTrack)), 'can only insert Channel model or JukeboxTrack object'

        self.inserted_media = media
        LOG.info(f'Media inserted: {str(media)} (type {str(type(media))})')

        if isinstance(media, Channel):
            self.set_mode_radio()

        if isinstance(media, JukeboxTrack):
            if self._playback_thread is not None:
                self._playback_thread.join()
                self._playback_thread = None
            self.jukebox.playing_track = self.inserted_media

            # self.set_mode_jukebox()

    def play(self):
        assert self.playback_proc is None, 'there is an active playback. stop() first.'

        if isinstance(self.inserted_media, Channel):
            assert self.inserted_media is not None, 'no media inserted. insert media first.'
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
                    self.set_mode_radio()

                    if self.radio.last_played is not None:
                        last_played_reset = self.radio.last_played
                        last_played_reset.last_played = False
                        last_played_reset.save()
                    # except Channel.DoesNotExist:
                    #     LOG.exception('Cannot reset last_played Channel:')

                    self.inserted_media.last_played = True
                    self.inserted_media.save()
                    # self.set_display_radio()
                else:
                    bad_channel = self.inserted_media
                    self.stop()
                    self.eject()
                    LOG.error(f'ffplay aborted inexpectedly, media ejected. Channel is not functional: {str(bad_channel)}')
                    raise Exception(f'ffplay aborted inexpectedly, media ejected. Channels is not functional: {str(bad_channel)}')
            else:
                LOG.error(f'Channel stream return code is not 200: {str(response.status)}')
                raise Exception(f'Channel stream return code is not 200: {str(response.status)}')

        else:
            assert self.mode == MODES['jukebox']['standby']['random'] \
                    or self.mode == MODES['jukebox']['standby']['album'] \
                    or self.mode == MODES['jukebox']['on_air']['random'] \
                    or self.mode == MODES['jukebox']['on_air']['album'], 'jukeoroni is not in jukebox mode. do it first'
            """
            Traceback (most recent call last):
              File "<input>", line 1, in <module>
              File "/data/django/jukeoroni/player/jukeoroni/jukeoroni.py", line 448, in play
                assert self.mode == MODES['jukebox']['standby'], 'jukebox is not in standby mode. do it first'
            AssertionError: jukebox is not in standby mode. do it first
            """
            LOG.info('setting jukebox mode to on_air')
            self.mode = MODES['jukebox']['on_air'][self.jukebox.loader_mode]
            self.set_display_jukebox()
            # self.state_watcher_thread()

        # elif isinstance(self.inserted_media, JukeboxTrack):
        #     self.jukebox_playback_thread()

    def pause(self):
        assert self.inserted_media is not None, 'no media inserted. insert media first.'
        assert self.playback_proc is not None, 'no playback is active. play() media first'
        assert self.playback_proc.poll() is None, 'playback_proc was terminated. start playback first'
        self.playback_proc.send_signal(signal.SIGSTOP)

        # TODO: pause icon overlay

    def resume(self):
        assert self.inserted_media is not None, 'no media inserted. insert media first.'
        assert self.playback_proc is not None, 'no playback is active. play() media first'
        assert self.playback_proc.poll() is None, 'playback_proc was terminated. start playback first'
        self.playback_proc.send_signal(signal.SIGCONT)

    def stop(self):
        assert isinstance(self.playback_proc, subprocess.Popen), 'nothing is playing'

        self.playback_proc.terminate()

        try:
            while self.playback_proc.poll() is None:
                time.sleep(0.1)
        except AttributeError:
            LOG.exception('playback_proc already terminated.')

        if isinstance(self.inserted_media, Channel):
            self.radio.is_on_air = None
            self.playback_proc.terminate()
            try:
                while self.playback_proc.poll() is None:
                    time.sleep(0.1)

            except AttributeError:
                # This is the expected behaviour
                pass

            self.playback_proc = None
            self.set_mode_radio()
            # self.set_display_radio()

        elif isinstance(self.inserted_media, JukeboxTrack):
            self.mode = MODES['jukebox']['standby'][self.jukebox.loader_mode]
            self.playback_proc.terminate()
            while self.playback_proc.poll() is None:
                time.sleep(0.1)
            self.playback_proc = None
            self.set_mode_jukebox()

        # self.playback_proc.terminate()
        # while self.playback_proc.poll() is None:
        #     time.sleep(0.1)
        # self.playback_proc = None
        # # self.

    def next(self, media=None):
        assert self.inserted_media is not None, 'Can only go to next if media is inserted.'
        assert self.playback_proc is not None, 'Can only go to next if media is playing.'
        assert media is None or isinstance(media, (Channel, JukeboxTrack)), 'can only insert Channel model'

        # convenience methods
        if isinstance(self.inserted_media, Channel):
            self.stop()

            success = False

            media = media or self.radio.random_channel

            while not success:
                try:
                    self.change_media(media)
                    self.play()
                    success = True
                except urllib.error.HTTPError:
                    LOG.exception(f'getting random channel. previous try with {str(media)} failed:')
                    media = self.radio.random_channel

        elif isinstance(self.inserted_media, JukeboxTrack):
            # raise NotImplementedError
            assert bool(self.jukebox.tracks), 'no jukebox track ready.'
            self.stop()
            self.eject()
            self.mode = MODES['jukebox']['on_air'][self.jukebox.loader_mode]
            # next track should be started by play thread
            # if not bool(self.jukebox.tracks):
            #     self.eject()
            #     return
            # self.change_media(media=media or self.jukebox.next_track)
            # self.play()

        else:
            raise NotImplementedError

    def previous(self):
        raise NotImplementedError

    def change_media(self, media):
        assert self.playback_proc is None, 'Can only change media while not playing'
        if isinstance(self.inserted_media, JukeboxTrack):
            raise NotImplementedError
        # convenience method
        self.eject()
        self.insert(media)

    def eject(self):
        assert self.inserted_media is not None, 'no media inserted. insert media first.'
        """
        [09-03-2021 11:41:38] [ERROR] [MainThread|3070003920] [player.jukeoroni.jukeoroni]: playback_proc already terminated.
        Traceback (most recent call last):
          File "/data/django/jukeoroni/player/jukeoroni/jukeoroni.py", line 474, in stop
            while self.playback_proc.poll() is None:
        AttributeError: 'NoneType' object has no attribute 'poll'
        Traceback (most recent call last):
          File "<input>", line 1, in <module>
          File "/data/django/jukeoroni/player/jukeoroni/jukeoroni.py", line 527, in next
            self.eject()
          File "/data/django/jukeoroni/player/jukeoroni/jukeoroni.py", line 548, in eject
            assert self.inserted_media is not None, 'no media inserted. insert media first.'
        AssertionError: no media inserted. insert media first.
        """

        """
        Traceback (most recent call last):
          File "<input>", line 1, in <module>
          File "/data/django/jukeoroni/player/jukeoroni/jukeoroni.py", line 527, in next
            self.eject()
          File "/data/django/jukeoroni/player/jukeoroni/jukeoroni.py", line 548, in eject
            assert self.inserted_media is not None, 'no media inserted. insert media first.'
        AssertionError: no media inserted. insert media first.
        """
        assert self.playback_proc is None, 'cannot eject media while playback is active. stop() first.'
        self.inserted_media = None
        self.jukebox.playing_track = None
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
        self.mode = MODES['jukeoroni']['standby']

        self.pimoroni_init()

        self.buttons_watcher_thread()
        self.pimoroni_watcher_thread()
        self.state_watcher_thread()

        self.set_display_turn_on()

    def _start_modules(self):
        # Radar
        self.layout_standby.radar.start(test=self.test)

        # Jukebox
        self.jukebox.turn_on()
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
        self.mode = MODES['jukeoroni']['off']

        # cannot join() the threads from
        # within the threads themselves
        LOG.info(f'Terminating self._pimoroni_watcher_thread...')
        self._pimoroni_watcher_thread.join()
        self._pimoroni_watcher_thread = None
        LOG.info(f'self._pimoroni_watcher_thread terminated')

        # LOG.info(f'Terminating self._state_watcher_thread...')
        # self._state_watcher_thread.join()
        # self._state_watcher_thread = None
        # LOG.info(f'self._state_watcher_thread terminated')

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

        # LOG.info(f'Terminating self.jukebox...')
        # self.jukebox.stop()
        # LOG.info(f'self.jukebox terminated')
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
        button_mapped = _BUTTON_MAPPINGS[button]
        LOG.info(f'Button press detected on pin: {pin} button: {button_mapped} ({button}), label: {self.LABELS[_BUTTON_PINS.index(pin)]}')

        if self.mode == MODES['jukeoroni']['off']:
            if button_mapped == 'X000':
                pass
            elif button_mapped == '0X00':
                pass
            elif button_mapped == '00X0':
                pass
            elif button_mapped == '000X':
                pass
                # self.turn_on()
        elif self.mode == MODES['jukeoroni']['standby']:
            if button_mapped == 'X000':
                print('X000')
                self.set_mode_jukebox()
            elif button_mapped == '0X00':
                self.set_mode_radio()
            elif button_mapped == '00X0':
                pass
            elif button_mapped == '000X':
                pass
        elif self.mode == MODES['radio']['standby']:
            if button_mapped == 'X000':
                self.set_mode_standby()
            elif button_mapped == '0X00':
                if self.inserted_media is None:
                    self.insert(media=self.radio.last_played)
                self.play()
            elif button_mapped == '00X0':
                pass
            elif button_mapped == '000X':
                pass
        elif self.mode == MODES['radio']['on_air']:
            if button_mapped == 'X000':
                self.stop()
            elif button_mapped == '0X00':
                self.next()
            elif button_mapped == '00X0':
                pass
            elif button_mapped == '000X':
                pass
        elif self.mode == MODES['jukebox']['standby']['random'] \
                or self.mode == MODES['jukebox']['standby']['album']:
            if button_mapped == 'X000':
                self.set_mode_standby()
            elif button_mapped == '0X00':
                self.play()
            elif button_mapped == '00X0':
                pass
            elif button_mapped == '000X':
                # random -> album; album -> random
                pass
        elif self.mode == MODES['jukebox']['on_air']['random'] \
                or self.mode == MODES['jukebox']['on_air']['album']:
            if button_mapped == 'X000':
                self.stop()
                self.set_mode_jukebox()
                # self.mode = MODES['jukebox']['standby']
            elif button_mapped == '0X00':
                self.next()
            elif button_mapped == '00X0':
                pass
            elif button_mapped == '000X':
                # random -> album; album -> random
                pass
    ############################################

    # ############################################
    # # playback process
    # def jukebox_playback_thread(self):
    #     self._jukebox_playback_thread = multiprocessing.Process(target=self._jukebox_playback_task)
    #     self._jukebox_playback_thread.name = 'Jukebox Playback Thread'
    #     self._jukebox_playback_thread.daemon = False
    #     self._jukebox_playback_thread.start()
    #
    # def _jukebox_playback_task(self):
    #     while self.on and self.mode == MODES['jukebox']['on_air_random']:
    #         self.playback_proc = subprocess.Popen(FFPLAY_CMD + [self.inserted_media.playing_from], shell=False)
    #
    #         time.sleep(1.0)
    # ############################################

    # ############################################
    # # State watcher (buttons)
    # # checks if the push of buttons or actions
    # # performed on web ui requires a state change
    # # TODO: define states
    # def state_watcher_thread(self):
    #     self._state_watcher_thread = threading.Thread(target=self._state_watcher_task)
    #     self._state_watcher_thread.name = 'State Watcher Thread'
    #     self._state_watcher_thread.daemon = False
    #     self._state_watcher_thread.start()
    #
    # def _state_watcher_task(self):
    #     update_interval = CLOCK_UPDATE_INTERVAL*60
    #     _waited = None
    #     while self.on:
    #         if _waited is None or _waited % update_interval == 0:
    #             _waited = 0
    #
    #         time.sleep(1.0)
    #         _waited += 1
    # ############################################
