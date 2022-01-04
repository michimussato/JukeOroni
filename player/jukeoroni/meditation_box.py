import logging

from player.jukeoroni.base_box import BaseBox
from player.jukeoroni.displays import Meditationbox as MeditationboxLayout
from player.jukeoroni.settings import (
    MEDITATION_DIR,
    ALBUM_TYPE_MEDITATION,
)


# class MeditationTrack(JukeboxTrack):
#     def __init__(self, django_track, cached=True):
#         super(MeditationTrack, self).__init__(django_track, cached)


class MeditationBox(BaseBox):

    def __init__(self, jukeoroni=None):
        super().__init__(jukeoroni)

        self.LOG = logging.getLogger(__name__)

        self.LOG.info(f'Initializing {self.box_type}...')

        # self.loader_mode = 'album'
        #
        # causes error: (maybe set_loader_mode_album()?)
        #
        # Exception in thread Track Loader Thread:
        # Traceback (most recent call last):
        #   File "/usr/lib/python3.7/threading.py", line 917, in _bootstrap_inner
        #     self.run()
        #   File "/usr/lib/python3.7/threading.py", line 865, in run
        #     self._target(*self._args, **self._kwargs)
        #   File "/data/django/jukeoroni/player/jukeoroni/base_box.py", line 210, in _track_loader_task
        #     loading_track = self.get_next_track()
        #   File "/data/django/jukeoroni/player/jukeoroni/base_box.py", line 325, in get_next_track
        #     first_album_track = self.playing_track.first_album_track
        # AttributeError: 'NoneType' object has no attribute 'first_album_track'

        self.layout = MeditationboxLayout()

    @property
    def box_type(self):
        return 'MeditationBox'

    @property
    def album_type(self):
        return ALBUM_TYPE_MEDITATION

    @property
    def audio_dir(self):
        return MEDITATION_DIR

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
