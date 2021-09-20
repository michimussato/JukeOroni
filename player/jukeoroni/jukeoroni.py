import time
import threading
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
    CLOCK_UPDATE_INTERVAL,
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


GPIO.setmode(GPIO.BCM)
GPIO.setup(_BUTTON_PINS, GPIO.IN, pull_up_down=GPIO.PUD_UP)


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

    def __init__(self, test=False):

        LOG.info(f'Initializing JukeOroni...')
        # TODO rename to headless
        self.test = test

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
        # self.current_time = None

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

    # def set_mode_radio(self):
    #     if self.radio.is_on_air:
    #         self.mode = MODES['radio']['on_air']
    #     elif not self.radio.is_on_air:
    #         self.mode = MODES['radio']['standby']
    #     self.set_display_radio()

    # def set_mode_jukebox(self):
    #     if self.playback_proc is not None:
    #         self.mode = MODES['jukebox']['on_air'][self.jukebox.loader_mode]
    #     elif self.playback_proc is None:
    #         self.mode = MODES['jukebox']['standby'][self.jukebox.loader_mode]
    #     # wait because inserted_media can be none
    #     # while playback_proc is not fully terminated
    #     # maybe just a temp hack
    #     # time.sleep(1.0)
    #     self.set_display_jukebox()
    #
    #     # if self._jukebox_playback_thread is None:
    #     #     self.jukebox_playback_thread()
    ############################################

    ############################################
    # display background handling
    # def pimoroni_init(self):
    #     self.pimoroni.__init__()
    #     GPIO.setmode(GPIO.BCM)
    #     GPIO.setup(_BUTTON_PINS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

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
            # self.pimoroni_init()
            LOG.info(f'Setting OFF Layout...')

            bg = self.layout_off.get_layout(labels=self.LABELS, cover=Resource().OFF_IMAGE_SQUARE)
            # self.set_image(image=bg)

            self.pimoroni.set_image(bg, saturation=PIMORONI_SATURATION)
            self.pimoroni.show(busy_wait=True)
            LOG.info(f'Setting OFF Layout: Done.')
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

            bg = self.radio.layout.get_layout(labels=self.LABELS, cover=self.radio.cover, title=self.radio.stream_title)
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

            # need to add None too, otherwise we might end up with
            # NoneType Error for self.inserted_media.cover_album
            if self.mode == MODES['jukebox']['standby']['album'] \
                    or self.mode == MODES['jukebox']['standby']['random']:
                bg = self.jukebox.layout.get_layout(labels=self.LABELS)
            elif self.mode == MODES['jukebox']['on_air']['album'] \
                    or self.mode == MODES['jukebox']['on_air']['random']:
                if self.inserted_media is None:
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
        radio_media_info_title_previous = None
        while True:

            new_time = localtime(now())
            # radio_media_info_title_previous = None
            # if self.mode == MODES['jukeoroni']['standby']:
            #     if self._current_time != new_time.strftime('%H:%M'):  # in stopped state
            #         if self._current_time is None or (int(new_time.strftime('%H:%M')[-2:])) % CLOCK_UPDATE_INTERVAL == 0:
            #             LOG.info('Display/Clock update.')
            #             self.set_image()
            #             self._current_time = new_time.strftime('%H:%M')

            # _msg_printed = False
            # while not self.jukebox.tracks and self.inserted_media is None:
            #     if not _msg_printed:
            #         LOG.info('waiting for a jukebox track...')
            #         # if self.mode == MODES['jukebox']['standby'] \
            #         #         or self.mode == MODES['jukebox']['on_air']:
            #         #     self.set_display_jukebox()
            #
            #         _msg_printed = True
            #
            #     time.sleep(1.0)
            # if _msg_printed:
            #     LOG.info('jukebox track loaded.')
            #     _msg_printed = False

            if self.mode == MODES['jukebox']['standby']['random'] \
                    or self.mode == MODES['jukebox']['standby']['album'] \
                    or self.mode == MODES['jukebox']['on_air']['random'] \
                    or self.mode == MODES['jukebox']['on_air']['album']:
                if self.inserted_media is None and bool(self.jukebox.tracks):
                    # try:
                    self.insert(self.jukebox.next_track)
                    # except AssertionError:
                    #     LOG.exception('No JukeBox track ready yet.')

            else:
                if isinstance(self.inserted_media, JukeboxTrack):
                    self.eject()

            if self.mode == MODES['jukebox']['standby']['random'] \
                    or self.mode == MODES['jukebox']['standby']['album']:
                if self._current_time != new_time.strftime('%H:%M'):
                    if self._current_time is None or (int(new_time.strftime('%H:%M')[-2:])) % CLOCK_UPDATE_INTERVAL == 0:
                        LOG.info('Display/Clock update.')
                        self.set_display_jukebox()
                        self._current_time = new_time.strftime('%H:%M')

            elif self.mode == MODES['jukebox']['on_air']['random'] \
                    or self.mode == MODES['jukebox']['on_air']['album']:

                # TODO implement Play/Next combo
                if self.playback_proc is None and isinstance(self.inserted_media, JukeboxTrack):
                    LOG.debug('Starting new playback thread')
                    self.jukebox_playback_thread()
                    # setting the timer for the display
                    # update to zero after a new track
                    # started
                    new_time = localtime(now())
                elif self.playback_proc is not None:
                    LOG.debug('Playback thread playback_proc is not None')
                    if self.playback_proc.poll() == 0:
                        LOG.debug('Jukebox playback not active, setting playback_proc to None.')
                        # process finished. join()?
                        self.playback_proc = None
                    elif self.playback_proc.poll() is None:
                        LOG.debug('Jukebox playback active.')
                        # still playing
                        pass

                if self._current_time != new_time.strftime('%H:%M'):  # in stopped state
                    if self._current_time is None or (int(new_time.strftime('%H:%M')[-2:])) % CLOCK_UPDATE_INTERVAL == 0:
                        LOG.info('Display/Clock update.')
                        self.set_display_jukebox()
                        self._current_time = new_time.strftime('%H:%M')

            # refresh radio display to updated clock, stream_title and radar
            elif self.mode == MODES['radio']['standby'] \
                    or self.mode == MODES['radio']['on_air']:
                if self._current_time != new_time.strftime('%H:%M'):  # in stopped state
                    if self._current_time is None \
                            or (int(new_time.strftime('%H:%M')[-2:])) % CLOCK_UPDATE_INTERVAL == 0 \
                            or radio_media_info_title_previous != self.radio.stream_title:
                        if radio_media_info_title_previous != self.radio.stream_title:
                            LOG.info('Stream info changed...')
                            LOG.info(f'Before: {radio_media_info_title_previous}')
                            LOG.info(f'New: {self.radio.stream_title}')
                        LOG.info('Display/Clock/Stream-Title update.')
                        self.set_display_radio()
                        radio_media_info_title_previous = self.radio.stream_title
                        self._current_time = new_time.strftime('%H:%M')

            elif self.mode == MODES['jukeoroni']['standby']:
                if self._current_time != new_time.strftime('%H:%M'):  # in stopped state
                    if self._current_time is None or (int(new_time.strftime('%H:%M')[-2:])) % CLOCK_UPDATE_INTERVAL == 0:
                        LOG.info('Display/Clock update.')
                        self.set_image()
                        self._current_time = new_time.strftime('%H:%M')

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
            pass
            # self.set_mode_radio()

        if isinstance(media, JukeboxTrack):
            if self._playback_thread is not None:
                self._playback_thread.join()
                self._playback_thread = None
            self.jukebox.playing_track = self.inserted_media

    def play(self):
        assert self.playback_proc is None, 'there is an active playback. stop() first.'

        if self.mode == MODES['radio']['on_air']:
            # self.mode == MODES['radio']['standby']:
            # self.insert(media=self.radio.last_played)
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

                if self.radio.last_played is not None:
                    last_played_reset = self.radio.last_played
                    last_played_reset.last_played = False
                    last_played_reset.save()

                self.radio.is_on_air = self.inserted_media

                self.radio.media_info_updater_thread(channel=self.inserted_media)
                self.playback_proc = subprocess.Popen(FFPLAY_CMD + [self.inserted_media.url], shell=False)
                try:
                    self.playback_proc.communicate(timeout=2.0)
                except subprocess.TimeoutExpired:
                    # this is the expected behaviour!!
                    LOG.info(f'ffplay started successfully. playing {str(self.inserted_media.display_name)}')
                    # self.set_mode_radio()

                    # if self.radio.last_played is not None:
                    #     last_played_reset = self.radio.last_played
                    #     last_played_reset.last_played = False
                    #     last_played_reset.save()
                    #
                    #  # except Channel.DoesNotExist:
                    #  #     LOG.exception('Cannot reset last_played Channel:')
                    #
                    self.inserted_media.last_played = True
                    self.inserted_media.save()
                    #  # self.set_display_radio()
                else:
                    bad_channel = self.inserted_media
                    self.stop()
                    self.eject()
                    LOG.error(f'ffplay aborted inexpectedly, media ejected. Channel is not functional: {str(bad_channel)}')
                    raise Exception(f'ffplay aborted inexpectedly, media ejected. Channels is not functional: {str(bad_channel)}')
            else:
                LOG.error(f'Channel stream return code is not 200: {str(response.status)}')
                raise Exception(f'Channel stream return code is not 200: {str(response.status)}')

        elif self.mode == MODES['jukebox']['standby']['random'] \
                or self.mode == MODES['jukebox']['standby']['album'] \
                or self.mode == MODES['jukebox']['on_air']['random'] \
                or self.mode == MODES['jukebox']['on_air']['album']:

            LOG.info('setting jukebox mode to on_air')
            self.mode = MODES['jukebox']['on_air'][self.jukebox.loader_mode]
            self.set_display_jukebox()

    # def pause(self):
    #     assert self.inserted_media is not None, 'no media inserted. insert media first.'
    #     assert self.playback_proc is not None, 'no playback is active. play() media first'
    #     assert self.playback_proc.poll() is None, 'playback_proc was terminated. start playback first'
    #     self.playback_proc.send_signal(signal.SIGSTOP)
    #
    #     # TODO: pause icon overlay
    #
    # def resume(self):
    #     assert self.inserted_media is not None, 'no media inserted. insert media first.'
    #     assert self.playback_proc is not None, 'no playback is active. play() media first'
    #     assert self.playback_proc.poll() is None, 'playback_proc was terminated. start playback first'
    #     self.playback_proc.send_signal(signal.SIGCONT)

    def stop(self):
        if isinstance(self.playback_proc, subprocess.Popen):
            self.playback_proc.terminate()

        if self.playback_proc is not None:
            try:
                while self.playback_proc.poll() is None:
                    time.sleep(0.1)
            except AttributeError:
                LOG.exception('playback_proc already terminated:')
            finally:
                self.playback_proc = None

        if isinstance(self.inserted_media, Channel):
            self.radio.is_on_air = None
            self.mode = MODES['radio']['standby']
            self.playback_proc = None
            self.set_display_radio()
            # self.set_mode_radio()

        # we need to be able to switch jukebox modes even when no
        # track was inserted yet; could be still loading
        elif isinstance(self.inserted_media, JukeboxTrack) \
                or self.mode == MODES['jukebox']['on_air'][self.jukebox.loader_mode]:
            self.mode = MODES['jukebox']['standby'][self.jukebox.loader_mode]
            self.playback_proc = None
            self.set_display_jukebox()

    def next(self, media=None):
        assert self.inserted_media is not None, 'Can only go to next if media is inserted.'
        assert self.playback_proc is not None, 'Can only go to next if media is playing.'
        assert media is None or isinstance(media, (Channel, JukeboxTrack)), 'can only insert Channel model'

        self.stop()

        # convenience methods
        if isinstance(self.inserted_media, Channel):

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
            # assert bool(self.jukebox.tracks), 'no jukebox track ready.'
            # self.stop()
            self.eject()
            # self.mode = MODES['jukebox']['on_air'][self.jukebox.loader_mode]
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
        # assert self.inserted_media is not None, 'no media inserted. insert media first.'
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

        # self.pimoroni_init()

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
                    LOG.info('New job in _pimoroni_thread_queue...')
                    # self.pimoroni_init()
                    thread = self._pimoroni_thread_queue
                    self._pimoroni_thread_queue = None
                    thread.start()

                    while thread.is_alive():
                        time.sleep(1.0)

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

            # def set_image_force(self, **kwargs):
            # self.pimoroni_init()

            if 'image' in kwargs:
                bg = kwargs['image']
            else:
                bg = self.layout_standby.get_layout(labels=self.LABELS)
            self.pimoroni.set_image(image=bg, saturation=PIMORONI_SATURATION)
            try:
                self.pimoroni.show(busy_wait=True)
                # self.pimoroni.show(busy_wait=False)
            except AttributeError:
                pass
                # LOG.exception('Pimoroni busy wait error')
            LOG.info(f'Setting Pimoroni image: Done.')
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

        # JukeOroni
        if self.mode == MODES['jukeoroni']['off']:
            if button_mapped == 'X000':
                pass
            elif button_mapped == '0X00':
                pass
            elif button_mapped == '00X0':
                pass
            elif button_mapped == '000X':
                pass
        elif self.mode == MODES['jukeoroni']['standby']:
            if button_mapped == 'X000':
                pass
                # self.mode = MODES['jukebox']['on_air'][self.jukebox.loader_mode]
                # self.set_display_jukebox()
                # # self.set_mode_jukebox()
            elif button_mapped == '0X00':
                self.mode = MODES['radio']['standby']
                self.set_display_radio()
                # self.set_mode_radio()
            elif button_mapped == '00X0':
                pass
            elif button_mapped == '000X':
                pass

        # Radio
        # TODO: pause/resume
        elif self.mode == MODES['radio']['standby']:
            if button_mapped == 'X000':
                self.eject()
                self.set_mode_standby()
            elif button_mapped == '0X00':
                if self.inserted_media is None:
                    if self.radio.last_played is None:
                        self.insert(media=self.radio.random_channel)
                    else:
                        self.insert(media=self.radio.last_played)
                self.mode = MODES['radio']['on_air']
                self.play()
            elif button_mapped == '00X0':
                pass
            elif button_mapped == '000X':
                pass
        elif self.mode == MODES['radio']['on_air']:
            if button_mapped == 'X000':
                self.mode = MODES['radio']['standby']
                self.stop()
            elif button_mapped == '0X00':
                self.next()
            elif button_mapped == '00X0':
                pass
            elif button_mapped == '000X':
                pass

        # # Jukebox
        # # TODO: pause/resume
        # elif self.mode == MODES['jukebox']['standby']['random']:
        #     if button_mapped == 'X000':
        #         self.eject()
        #         self.set_mode_standby()
        #     elif button_mapped == '0X00':
        #         self.play()
        #     elif button_mapped == '00X0':
        #         pass
        #     elif button_mapped == '000X':
        #         self.jukebox.set_loader_mode_album()
        #         self.mode = MODES['jukebox']['standby'][self.jukebox.loader_mode]
        # elif self.mode == MODES['jukebox']['standby']['album']:
        #     if button_mapped == 'X000':
        #         self.set_mode_standby()
        #     elif button_mapped == '0X00':
        #         self.play()
        #     elif button_mapped == '00X0':
        #         pass
        #     elif button_mapped == '000X':
        #         self.jukebox.set_loader_mode_random()
        #         self.mode = MODES['jukebox']['standby'][self.jukebox.loader_mode]

        # elif self.mode == MODES['jukebox']['on_air']['random']:
        #     if button_mapped == 'X000':
        #         self.stop()
        #         self.set_mode_jukebox()
        #     elif button_mapped == '0X00':
        #         self.next()
        #     elif button_mapped == '00X0':
        #         pass
        #     elif button_mapped == '000X':
        #         self.jukebox.set_loader_mode_album()
        #         self.set_mode_jukebox()
        # elif self.mode == MODES['jukebox']['on_air']['album']:
        #     if button_mapped == 'X000':
        #         self.stop()
        #         self.set_mode_jukebox()
        #     elif button_mapped == '0X00':
        #         self.next()
        #     elif button_mapped == '00X0':
        #         pass
        #     elif button_mapped == '000X':
        #         self.jukebox.set_loader_mode_random()
        #         self.set_mode_jukebox()
    ############################################
