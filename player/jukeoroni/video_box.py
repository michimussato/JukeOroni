import logging
import os.path

from omxplayer.player import OMXPlayer
from pathlib import Path

from player.jukeoroni.base_box import BaseBox
from player.jukeoroni.displays import Videobox as VideoboxLayout
from player.jukeoroni.settings import Settings


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

        self.omxplayer = OMXPlayer(self.video_file,
                                   args=['--no-keys', '--adev', Settings.AUDIO_OUT],
                                   # dbus_name='org.mpris.MediaPlayer2.omxplayer1',
                                   pause=True,
                                   )
        self.omxplayer.playEvent += lambda _: self.LOG.info("Play")
        self.omxplayer.pauseEvent += lambda _: self.LOG.info("Pause")
        self.omxplayer.stopEvent += lambda _: self.LOG.info("Stop")
        # self.omxplayer.pause()

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
    def video_file(self):
        return os.path.join(self.video_dir, 'Guardians of the Galaxy (2014)', 'Guardians.of.the.Galaxy.2014.720p.BluRay.x264.YIFY.mp4')

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
        return NotImplementedError

    def get_next_track(self):
        return NotImplementedError

    def kill_loading_process(self):
        return NotImplementedError
