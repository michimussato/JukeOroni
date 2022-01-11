import logging

from player.jukeoroni.base_box import BaseBox
from player.jukeoroni.displays import Meditationbox as MeditationboxLayout
from player.jukeoroni.settings import (
    MEDITATION_DIR,
    ALBUM_TYPE_MEDITATION,
    MODES
)


# class MeditationTrack(JukeboxTrack):
#     def __init__(self, django_track, cached=True):
#         super(MeditationTrack, self).__init__(django_track, cached)


class MeditationBox(BaseBox):

    def __init__(self, jukeoroni=None):
        super().__init__(jukeoroni)

        self.LOG = logging.getLogger(__name__)

        self.LOG.info(f'Initializing {self.box_type}...')

        self.set_loader_mode_album()
        self._need_first_album_track = True

        self.layout = MeditationboxLayout()

    @property
    def box_type(self):
        return 'meditationbox'

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
