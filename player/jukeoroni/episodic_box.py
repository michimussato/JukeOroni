import logging

from player.jukeoroni.base_box import BaseBox
from player.jukeoroni.displays import Audiobookbox as AudiobookboxLayout
from player.jukeoroni.settings import Settings  # (
#     AUDIOBOOK_DIR,
#     ALBUM_TYPE_AUDIOBOOK,
# )


class EpisodicBox(BaseBox):
    """
from player.jukeoroni.juke_box import Jukebox
box = Jukebox()
box.turn_on()

box.set_auto_update_tracklist_on()


box.turn_off()
    """
    def __init__(self, jukeoroni=None):
        super().__init__(jukeoroni)

        self.LOG = logging.getLogger(__name__)

        self.LOG.info(f'Initializing {self.box_type}...')

        self.set_loader_mode_album()
        self._need_first_album_track = True

        self.layout = AudiobookboxLayout()

    @property
    def box_type(self):
        return 'episodicbox'

    # @property
    # def album_type(self):
    #     return ALBUM_TYPE_AUDIOBOOK

    # @property
    # def audio_dir(self):
    #     return AUDIOBOOK_DIR
