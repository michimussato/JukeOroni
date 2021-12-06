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
    STATE_WATCHER_CADENCE,
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


GPIO.setwarnings(True)
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

        self.paused = False

        self.on = False
        self.mode = None
        self.set_mode_off()

        self.jukebox = Box(jukeoroni=self)
        self.radio = Radio()

        self.playback_proc = None
        self.inserted_media = None

        self._flag_next = False
        self._next = None

        self.pimoroni = Inky()

        self._current_time = None

        # display layouts
        self.layout_off = OffLayout()
        self.layout_standby = StandbyLayout()
        self.layout_radio = self.radio.layout
        self._loading_display_activated = False

        self._pimoroni_thread_queue = None

        # Watcher threads
        self._pimoroni_watcher_thread = None
        self._buttons_watcher_thread = None
        self._state_watcher_thread = None

        self._jukebox_playback_thread = None
        self._playback_thread = None

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
    ############################################

    ############################################
    #  display background handling
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
            self.set_image()
        else:
            LOG.info(f'Not setting TURN_ON image. Test mode.')

    def set_display_turn_off(self):
        """
        j.set_display_turn_off()
        """
        assert not self.on, 'JukeOroni needs to be turned off first.'
        if not self.test:
            LOG.info(f'Setting OFF Layout...')

            bg = self.layout_off.get_layout(labels=self.LABELS, cover=Resource().OFF_IMAGE_SQUARE)

            self.pimoroni.set_image(bg, saturation=PIMORONI_SATURATION)
            # self.pimoroni.set_image(bg)
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

            bg = self.layout_radio.get_layout(labels=self.LABELS, cover=self.radio.cover, title=self.radio.stream_title)
            self.set_image(image=bg)

    def set_display_jukebox(self):
        """
        j.set_display_jukebox()
        """
        if not self.test:

            # need to add None too, otherwise we might end up with
            # NoneType Error for self.inserted_media.cover_album
            if self.mode == MODES['jukebox']['standby']['album'] \
                    or self.mode == MODES['jukebox']['standby']['random']:
                bg = self.jukebox.layout.get_layout(labels=self.LABELS)
            elif self.mode == MODES['jukebox']['on_air']['album'] \
                    or self.mode == MODES['jukebox']['on_air']['random']:
                try:
                    bg = self.jukebox.layout.get_layout(labels=self.LABELS, cover=self.inserted_media.cover_album,
                                                        artist=self.inserted_media.cover_artist)
                except AttributeError:
                    bg = self.jukebox.layout.get_layout(labels=self.LABELS, loading=True)
                    LOG.exception('inserted_media problem: ')
            self.set_image(image=bg)
    ############################################

    """
Nov  1 19:46:25 jukeoroni gunicorn[1374]: Exception in thread State Watcher Thread:
Nov  1 19:46:25 jukeoroni gunicorn[1374]: Traceback (most recent call last):
Nov  1 19:46:25 jukeoroni gunicorn[1374]:   File "/usr/lib/python3.7/urllib/request.py", line 1324, in do_open
Nov  1 19:46:25 jukeoroni gunicorn[1374]:     encode_chunked=req.has_header('Transfer-encoding'))
Nov  1 19:46:25 jukeoroni gunicorn[1374]:   File "/usr/lib/python3.7/http/client.py", line 1260, in request
Nov  1 19:46:25 jukeoroni gunicorn[1374]:     self._send_request(method, url, body, headers, encode_chunked)
Nov  1 19:46:25 jukeoroni gunicorn[1374]:   File "/usr/lib/python3.7/http/client.py", line 1306, in _send_request
Nov  1 19:46:25 jukeoroni gunicorn[1374]:     self.endheaders(body, encode_chunked=encode_chunked)
Nov  1 19:46:25 jukeoroni gunicorn[1374]:   File "/usr/lib/python3.7/http/client.py", line 1255, in endheaders
Nov  1 19:46:25 jukeoroni gunicorn[1374]:     self._send_output(message_body, encode_chunked=encode_chunked)
Nov  1 19:46:25 jukeoroni gunicorn[1374]:   File "/usr/lib/python3.7/http/client.py", line 1030, in _send_output
Nov  1 19:46:25 jukeoroni gunicorn[1374]:     self.send(msg)
Nov  1 19:46:25 jukeoroni gunicorn[1374]:   File "/usr/lib/python3.7/http/client.py", line 970, in send
Nov  1 19:46:25 jukeoroni gunicorn[1374]:     self.connect()
Nov  1 19:46:25 jukeoroni gunicorn[1374]:   File "/usr/lib/python3.7/http/client.py", line 942, in connect
Nov  1 19:46:25 jukeoroni gunicorn[1374]:     (self.host,self.port), self.timeout, self.source_address)
Nov  1 19:46:25 jukeoroni gunicorn[1374]:   File "/usr/lib/python3.7/socket.py", line 707, in create_connection
Nov  1 19:46:25 jukeoroni gunicorn[1374]:     for res in getaddrinfo(host, port, 0, SOCK_STREAM):
Nov  1 19:46:25 jukeoroni gunicorn[1374]:   File "/usr/lib/python3.7/socket.py", line 748, in getaddrinfo
Nov  1 19:46:25 jukeoroni gunicorn[1374]:     for res in _socket.getaddrinfo(host, port, family, type, proto, flags):
Nov  1 19:46:25 jukeoroni gunicorn[1374]: socket.gaierror: [Errno -3] Temporary failure in name resolution
Nov  1 19:46:25 jukeoroni gunicorn[1374]: During handling of the above exception, another exception occurred:
Nov  1 19:46:25 jukeoroni gunicorn[1374]: Traceback (most recent call last):
Nov  1 19:46:25 jukeoroni gunicorn[1374]:   File "/usr/lib/python3.7/threading.py", line 917, in _bootstrap_inner
Nov  1 19:46:25 jukeoroni gunicorn[1374]:     self.run()
Nov  1 19:46:25 jukeoroni gunicorn[1374]:   File "/usr/lib/python3.7/threading.py", line 865, in run
Nov  1 19:46:25 jukeoroni gunicorn[1374]:     self._target(*self._args, **self._kwargs)
Nov  1 19:46:25 jukeoroni gunicorn[1374]:   File "/data/django/jukeoroni/player/jukeoroni/jukeoroni.py", line 292, in state_watcher_task
Nov  1 19:46:25 jukeoroni gunicorn[1374]:     self.play()
Nov  1 19:46:25 jukeoroni gunicorn[1374]:   File "/data/django/jukeoroni/player/jukeoroni/jukeoroni.py", line 435, in play
Nov  1 19:46:25 jukeoroni gunicorn[1374]:     response = urllib.request.urlopen(req)
Nov  1 19:46:25 jukeoroni gunicorn[1374]:   File "/usr/lib/python3.7/urllib/request.py", line 222, in urlopen
Nov  1 19:46:25 jukeoroni gunicorn[1374]:     return opener.open(url, data, timeout)
Nov  1 19:46:25 jukeoroni gunicorn[1374]:   File "/usr/lib/python3.7/urllib/request.py", line 525, in open
Nov  1 19:46:25 jukeoroni gunicorn[1374]:     response = self._open(req, data)
Nov  1 19:46:25 jukeoroni gunicorn[1374]:   File "/usr/lib/python3.7/urllib/request.py", line 543, in _open
Nov  1 19:46:25 jukeoroni gunicorn[1374]:     '_open', req)
Nov  1 19:46:25 jukeoroni gunicorn[1374]:   File "/usr/lib/python3.7/urllib/request.py", line 503, in _call_chain
Nov  1 19:46:25 jukeoroni gunicorn[1374]:     result = func(*args)
Nov  1 19:46:25 jukeoroni gunicorn[1374]:   File "/usr/lib/python3.7/urllib/request.py", line 1352, in http_open
Nov  1 19:46:25 jukeoroni gunicorn[1374]:     return self.do_open(http.client.HTTPConnection, req)
Nov  1 19:46:25 jukeoroni gunicorn[1374]:   File "/usr/lib/python3.7/urllib/request.py", line 1326, in do_open
Nov  1 19:46:25 jukeoroni gunicorn[1374]:     raise URLError(err)
Nov  1 19:46:25 jukeoroni gunicorn[1374]: urllib.error.URLError: <urlopen error [Errno -3] Temporary failure in name resolution>
    """
    def state_watcher_thread(self):
        self._state_watcher_thread = threading.Thread(target=self.state_watcher_task)
        self._state_watcher_thread.name = 'State Watcher Thread'
        self._state_watcher_thread.daemon = False
        self._state_watcher_thread.start()

    def state_watcher_task(self):
        # assert self.jukebox.on, 'turn on jukebox before initiating state_watcher_task'
        radio_media_info_title_previous = None

        previous_mode = None
        update_mode = True
        # display_loading = False

        while True:

            if self._flag_next:
                self.next(self._next)
                self._flag_next = False
                self._next = None

            if previous_mode == self.mode and previous_mode is not None:
                update_mode = False
            else:
                update_mode = True
                LOG.info('Mode changed')
                previous_mode = self.mode
                LOG.debug(self.mode)

            new_time = localtime(now())

            # JUKEORONI
            if self.mode == MODES['jukeoroni']['standby']:
                if update_mode:
                    update_mode = False
                    self.stop()
                    self.eject()
                    self.set_display_standby()
                else:
                    if self._current_time != new_time.strftime('%H:%M'):  # in stopped state
                        if self._current_time is None or (int(new_time.strftime('%H:%M')[-2:])) % CLOCK_UPDATE_INTERVAL == 0:
                            LOG.info('Display/Clock update.')
                            self.set_display_standby()
                            self._current_time = new_time.strftime('%H:%M')

            # RADIO
            elif self.mode == MODES['radio']['standby'] \
                    or self.mode == MODES['radio']['on_air']:

                if update_mode:
                    update_mode = False

                    if self.mode == MODES['radio']['standby']:
                        self.stop()
                        self.eject()
                        self.set_display_radio()

                    elif self.mode == MODES['radio']['on_air']:
                        if self._next is not None:
                            self.insert(media=self._next)
                            self._next = None
                        if self.inserted_media is None:
                            if self.radio.last_played is None:
                                self.insert(media=self.radio.random_channel)
                            else:
                                self.insert(media=self.radio.last_played)
                        self.play()
                        self.set_display_radio()
                else:
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

            # JUKEBOX STANDBY
            elif self.mode == MODES['jukebox']['standby']['random'] \
                    or self.mode == MODES['jukebox']['standby']['album']:

                if update_mode:
                    update_mode = False

                    if self.mode == MODES['jukebox']['standby']['random']:
                        self.stop()
                        self.eject()
                        if self.jukebox.loader_mode != 'random':
                            self.jukebox.set_loader_mode_random()
                        # self.set_display_jukebox()

                    elif self.mode == MODES['jukebox']['standby']['album']:
                        self.stop()
                        self.eject()
                        if self.jukebox.loader_mode != 'album':
                            self.jukebox.set_loader_mode_album()

                    self.set_display_jukebox()

                else:
                    if self._current_time != new_time.strftime('%H:%M'):
                        if self._current_time is None or (int(new_time.strftime('%H:%M')[-2:])) % CLOCK_UPDATE_INTERVAL == 0:
                            LOG.info('Display/Clock update.')
                            self.set_display_jukebox()
                            self._current_time = new_time.strftime('%H:%M')

            # JUKEBOX ON_AIR
            elif self.mode == MODES['jukebox']['on_air']['random'] \
                    or self.mode == MODES['jukebox']['on_air']['album']:

                # Make sure, jukebox keeps playing if in mode without
                # considering the update_mode flag

                if self.mode == MODES['jukebox']['on_air']['random']:
                    if self.jukebox.loader_mode != 'random':
                        self.jukebox.set_loader_mode_random()
                    # self.play_jukebox()
                    # LOG.info(f'Playing: {self.jukebox.playing_track}')

                elif self.mode == MODES['jukebox']['on_air']['album']:
                    if self.jukebox.loader_mode != 'album':
                        self.jukebox.set_loader_mode_album()

                self.play_jukebox()
                # LOG.info(f'Playing: {self.jukebox.playing_track}')

                if update_mode:
                    update_mode = False
                    self.set_display_jukebox()

                else:
                    if self._current_time != new_time.strftime('%H:%M'):
                        if self._current_time is None or (int(new_time.strftime('%H:%M')[-2:])) % CLOCK_UPDATE_INTERVAL == 0:
                            LOG.info('Display/Clock update.')
                            self.set_display_jukebox()
                            self._current_time = new_time.strftime('%H:%M')

            time.sleep(STATE_WATCHER_CADENCE)

    def play_jukebox(self):
        if self.jukebox.playing_track is not None:
            return
        elif not bool(self.jukebox.tracks):  # and self.playback_proc is None:
            LOG.info('No tracks ready')
            if self.jukebox.loading_track is not None:
                LOG.info('Loading 1st track...')
                if not self._loading_display_activated:
                    self.set_display_jukebox()
                    self._loading_display_activated = True
            else:
                LOG.warning('Not loading!!!')
            # print('no tracks ready')
            return

        self._loading_display_activated = False

        if self.inserted_media is None:  # and bool(self.jukebox.tracks):
            self.insert(self.jukebox.next_track)

        # TODO implement Play/Next combo
        if isinstance(self.inserted_media, JukeboxTrack):
            LOG.debug('Starting new playback thread')
            self.jukebox_playback_thread()
            self.set_display_jukebox()

            time.sleep(1.0)

    def jukebox_playback_thread(self):
        assert isinstance(self.inserted_media, JukeboxTrack)

        self._playback_thread = threading.Thread(target=self._playback_task)
        self._playback_thread.name = 'Playback Thread'
        self._playback_thread.daemon = False
        self._playback_thread.start()

    def _playback_task(self):
        LOG.info(f'starting playback thread: for {self.inserted_media.path} from {self.inserted_media.playing_from}')  # TODO add info
        self.jukebox.playing_track = self.inserted_media
        self.inserted_media.play(jukeoroni=self)
        self.jukebox.playing_track = None
        LOG.info('playback finished')
        self.eject()
        self._playback_thread = None
        self._jukebox_playback_thread = None
    ############################################

    ############################################
    # playback workflow
    def insert(self, media):
        # j.insert(j.radio.last_played)
        assert self.on, 'JukeOroni is OFF. turn_on() first.'
        assert self.inserted_media is None, f'There is a medium inserted already: {self.inserted_media}'
        # TODO: add types to tuple
        assert isinstance(media, (Channel, JukeboxTrack)), 'can only insert Channel model or JukeboxTrack object'

        self.inserted_media = media
        LOG.info(f'Media inserted: {str(media)} (type {str(type(media))})')

        if isinstance(media, Channel):
            pass

        elif isinstance(media, JukeboxTrack):
            if self._playback_thread is not None:
                self._playback_thread.join()
                self._playback_thread = None
            self.jukebox.playing_track = self.inserted_media

    def play(self):
        assert self.playback_proc is None, 'there is an active playback. stop() first.'

        if self.mode == MODES['radio']['on_air']:
            assert self.inserted_media is not None, 'no media inserted. insert media first.'
            hdr = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}
            req = urllib.request.Request(self.inserted_media.url, headers=hdr)
            try:
                # test if url is reachable
                response = urllib.request.urlopen(req)
            except urllib.error.HTTPError as err:
                bad_channel = self.inserted_media
                LOG.exception(f'Could not open URL: {str(bad_channel)}')
                self.stop()
                self.eject()
                bad_channel.last_played = False
                bad_channel.save()
                self.mode = MODES['radio']['standby']
                self.set_display_radio()
                return

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

                    self.inserted_media.last_played = True
                    self.inserted_media.save()

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
        self.paused = True

        # TODO: pause icon overlay

    def resume(self):
        assert self.inserted_media is not None, 'no media inserted. insert media first.'
        assert self.playback_proc is not None, 'no playback is active. play() media first'
        assert self.playback_proc.poll() is None, 'playback_proc was terminated. start playback first'
        self.playback_proc.send_signal(signal.SIGCONT)
        self.paused = False

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

        LOG.info(f'inserted_media is: {self.inserted_media}')

        if isinstance(self.inserted_media, Channel):
            self.radio.is_on_air = None
            self.playback_proc = None

        # we need to be able to switch jukebox modes even when no
        # track was inserted yet; could be still loading
        elif isinstance(self.inserted_media, JukeboxTrack) \
                or self.mode == MODES['jukebox']['on_air'][self.jukebox.loader_mode]:

            self.playback_proc = None

    def next(self, media=None):
        assert self.inserted_media is not None, 'Can only go to next if media is inserted.'
        # assert self.playback_proc is not None, 'Can only go to next if media is playing.'
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

            self.set_display_radio()

        elif isinstance(self.inserted_media, JukeboxTrack):
            self.eject()
            self.set_display_jukebox()

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
                   self.mode['buttons']['X000'],
                   self.mode['buttons']['0X00'],
                   self.mode['buttons']['00X0'],
                   self.mode['buttons']['000X'],
               ][::-1]  # reversed for readabilty (from left to right)

    ############################################
    # startup procedure
    def turn_on(self, disable_track_loader=False):
        assert not self.on, 'JukeOroni is ON already'
        self._start_jukeoroni()
        self._start_modules(disable_track_loader)

    def _start_jukeoroni(self):
        self.on = True
        self.mode = MODES['jukeoroni']['standby']

        # self.pimoroni_init()

        self.buttons_watcher_thread()
        self.pimoroni_watcher_thread()
        self.state_watcher_thread()

        self.set_display_turn_on()

    def _start_modules(self, disable_track_loader):
        # Radar
        self.layout_standby.radar.start(test=self.test)

        # Jukebox
        self.jukebox.turn_on(disable_track_loader)
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

            if 'image' in kwargs:
                bg = kwargs['image']
            else:
                bg = self.layout_standby.get_layout(labels=self.LABELS)
            # self.pimoroni.set_image(image=bg, saturation=PIMORONI_SATURATION)
            self.pimoroni.set_image(image=bg)
            try:
                self.pimoroni.show(busy_wait=True)
            except RuntimeError:  # AttributeError?
                pass
            LOG.info(f'Setting Pimoroni image: Done.')
    ############################################

    ############################################
    # # buttons_watcher_thread
    def buttons_watcher_thread(self):
        for pin in _BUTTON_PINS:
            # the callback function starts a new thread in the background
            GPIO.add_event_detect(pin, GPIO.FALLING, self._handle_button, bouncetime=500)

    def _handle_button(self, pin):
        button = _BUTTON_PINS.index(pin)
        button_mapped = _BUTTON_MAPPINGS[button]
        LOG.info(f'Button press detected on pin: {pin} button: {button_mapped} ({button}), label: {self.LABELS[_BUTTON_PINS.index(pin)]}')

        # JukeOroni
        if self.mode == MODES['jukeoroni']['off']:
            if button_mapped == 'X000':
                return
            elif button_mapped == '0X00':
                return
            elif button_mapped == '00X0':
                return
            elif button_mapped == '000X':
                return
            return
        elif self.mode == MODES['jukeoroni']['standby']:
            if button_mapped == 'X000':
                self.mode = MODES['jukebox']['standby'][self.jukebox.loader_mode]
                return
            elif button_mapped == '0X00':
                self.mode = MODES['radio']['standby']
                return
            elif button_mapped == '00X0':
                return
            elif button_mapped == '000X':
                return
            return

        # Radio
        # TODO: pause/resume
        elif self.mode == MODES['radio']['standby']:
            if button_mapped == 'X000':
                self.mode = MODES['jukeoroni']['standby']
                return
            elif button_mapped == '0X00':
                self.mode = MODES['radio']['on_air']
                return
            elif button_mapped == '00X0':
                return
            elif button_mapped == '000X':
                return
            return
        elif self.mode == MODES['radio']['on_air']:
            if button_mapped == 'X000':
                self.mode = MODES['radio']['standby']
                return
            elif button_mapped == '0X00':
                self._flag_next = True
                return
            elif button_mapped == '00X0':
                return
            elif button_mapped == '000X':
                return
            return

        # Jukebox
        # TODO: pause/resume
        elif self.mode == MODES['jukebox']['standby']['random']:
            if button_mapped == 'X000':
                self.mode = MODES['jukeoroni']['standby']
                return
            elif button_mapped == '0X00':
                self.mode = MODES['jukebox']['on_air']['random']
                return
            elif button_mapped == '00X0':
                return
            elif button_mapped == '000X':
                self.mode = MODES['jukebox']['standby']['album']
                return
            return
        elif self.mode == MODES['jukebox']['standby']['album']:
            if button_mapped == 'X000':
                self.mode = MODES['jukeoroni']['standby']
                return
            elif button_mapped == '0X00':
                self.mode = MODES['jukebox']['on_air']['album']
                return
            elif button_mapped == '00X0':
                return
            elif button_mapped == '000X':
                self.mode = MODES['jukebox']['standby']['random']
                return
            return

        elif self.mode == MODES['jukebox']['on_air']['random']:
            if button_mapped == 'X000':
                self.mode = MODES['jukebox']['standby']['random']
                return
            elif button_mapped == '0X00':
                self._flag_next = True
                return
            elif button_mapped == '00X0':
                return
            elif button_mapped == '000X':
                self.mode = MODES['jukebox']['on_air']['album']
                return
            return
        elif self.mode == MODES['jukebox']['on_air']['album']:
            if button_mapped == 'X000':
                self.mode = MODES['jukebox']['standby']['album']
                return
            elif button_mapped == '0X00':
                self._flag_next = True
                return
            elif button_mapped == '00X0':
                return
            elif button_mapped == '000X':
                self.mode = MODES['jukebox']['on_air']['random']
                return
            return
        return
    ############################################
