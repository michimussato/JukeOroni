import logging
import os.path
import random
import threading
import time

from omxplayer.player import OMXPlayer
# from pathlib import Path

from player.jukeoroni.base_box import BaseBox
from player.jukeoroni.displays import Videobox as VideoboxLayout
from player.jukeoroni.settings import Settings
from player.models import Video


# class MeditationTrack(JukeboxTrack):
#     def __init__(self, django_track, cached=True):
#         super(MeditationTrack, self).__init__(django_track, cached)


class VideoBox(BaseBox):

    def __init__(self, jukeoroni=None):
        super().__init__(jukeoroni)

        self.LOG = logging.getLogger(__name__)

        self.LOG.info(f'Initializing {self.box_type}...')

        self.loader_mode = 'random'

        # self.set_loader_mode_album()
        # self._need_first_album_track = True

        self.layout = VideoboxLayout()

        self.omxplayer = None
        self._omx_player_watcher_thread = None
        self._omxplayer_thread = None

        self.omx_player_watcher_thread()

    def omx_player_watcher_thread(self):
        self._omx_player_watcher_thread = threading.Thread(target=self._omx_player_watcher_task)
        self._omx_player_watcher_thread.name = 'OMXPlayer Watcher Thread'
        self._omx_player_watcher_thread.daemon = False
        self._omx_player_watcher_thread.start()

    def _omx_player_watcher_task(self):

        while True:

            if self.omxplayer is None:
                self.LOG.info('OMXPlayer not playing yet...')
                time.sleep(1.0)
                continue

            status = self.omxplayer.playback_status()

            if status == 'Playing':
                self.LOG.debug('OMXPlayer is currently playing...')
                time.sleep(1.0)
                continue
            elif status == 'Paused':
                self.LOG.debug('OMXPlayer is currently paused...')
                time.sleep(1.0)
                continue

            # Todo?
            #  status == 'Stopped'?

            # self.LOG.info('OMXPlayer finished playing.')
            #
            # self.omxplayer.quit()
            # self._omxplayer_thread.join()
            # self.omxplayer = None
            #
            # self.LOG.info('O')

            time.sleep(1.0)

    def omx_player_thread(self, video_file):
        self._omxplayer_thread = threading.Thread(target=self._omxplayer_task, args=(video_file,))
        self._omxplayer_thread.name = 'OMXPlayer Playback Thread'
        self._omxplayer_thread.daemon = False
        self._omxplayer_thread.start()

        # while self.omxplayer is None:
        #     self.LOG.info('OMXPlayer not playing yet...')
        #     time.sleep(0.5)
        #
        # while self.omxplayer.playback_status() in ['Playing', 'Paused']:
        #     time.sleep(1.0)
        #     self.LOG.debug('OMXPlayer is still playing...')
        # self.LOG.info('OMXPlayer finished playing.')
        #
        # self.omxplayer.quit()
        # self._omxplayer_thread.join()
        # self.omxplayer = None

    def _omxplayer_task(self, video_file):

        if self.omxplayer is None:
            # self.omxplayer = None



            self.omxplayer = OMXPlayer(video_file,
                                       args=['--no-keys', '--adev', Settings.AUDIO_OUT],
                                       # dbus_name='org.mpris.MediaPlayer2.omxplayer1',
                                       pause=True,
                                       )
            self.omxplayer.playEvent += lambda _: self.LOG.info("Play")
            self.omxplayer.pauseEvent += lambda _: self.LOG.info("Pause")
            self.omxplayer.stopEvent += lambda _: self.LOG.info("Stop")

        else:
            self.omxplayer.load(video_file, pause=True)


        # while self.omxplayer.is_playing():
        #     time.sleep(1.0)
        #     self.LOG('OMXPlayer is still playing...')
        #
        # self.omxplayer.quit()
        # self.



    @property
    def file_filter(self):
        return Settings.VIDEO_FILTER

    @property
    def box_type(self):
        return 'videobox'

    @property
    def album_type(self):
        return None

    @property
    def audio_dir(self):
        return self.video_dir

    @property
    def video_dir(self):
        return Settings.VIDEO_DIR

    @property
    def video_list(self):
        # import fnmatch
        # import os
        # return Video.objects.filter(album__album_type=self.album_type)
        return Video.objects.all()

        # results = []
        # for root, dirs, files in os.walk(os.path.join(Settings.VIDEO_DIR, 'torrents')):
        #     for _file in files:
        #         for video_filter in Settings.VIDEO_FILTER:
        #             if video_filter in os.path.splitext(_file)[1]:
        #         # if any([i for i in Settings.VIDEO_FILTER if i in os.path.splitext(_file)]):
        #         # # if fnmatch.fnmatch(_file, Settings.VIDEO_FILTER):
        #                 results.append(os.path.join(root, _file))
        # return results

    @property
    def video_file(self):
        # raise Exception(self.videos)
        # import pdb; pdb.set_trace()
        video = self.video_list[random.randint(1, len(self.video_list))-1]
        return os.path.join(Settings.VIDEO_DIR, video.video_source)
        # return os.path.join(self.video_dir, 'Guardians of the Galaxy (2014)', 'Guardians.of.the.Galaxy.2014.720p.BluRay.x264.YIFY.mp4')

    # # We could set a default Meditation Album like so:
    # @property
    # def requested_album_id(self):
    #     some_id = 12345
    #     return some_id
    #
    # @requested_album_id.setter
    # def requested_album_id(self, i):
    #     # overrides/ignores
    #     # self.requested_album_id = None
    #     # (does nothing but prevents error)
    #     pass

    # def temp_cleanup(self):
    #     pass

    # OVERRIDES
    def set_loader_mode_album(self):
        return NotImplementedError

    def set_loader_mode_random(self):
        return NotImplementedError

    def play_album(self, album_id):
        return NotImplementedError

    def play_track(self, track_id):
        return NotImplementedError

    def set_auto_update_tracklist_on(self):
        return NotImplementedError

    def set_auto_update_tracklist_off(self):
        return NotImplementedError

    def track_list_generator_thread(self):
        return NotImplementedError

    def track_list_generator_task(self):
        return NotImplementedError

    def track_loader_thread(self):
        return NotImplementedError

    def _track_loader_task(self):
        return NotImplementedError

    def track_list(self):
        # return
        return NotImplementedError

    def get_next_track(self):
        return NotImplementedError

    def kill_loading_process(self):
        return NotImplementedError
