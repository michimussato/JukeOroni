import logging

from player.jukeoroni.base_box import BaseBox
from player.jukeoroni.displays import Jukebox as JukeboxLayout
from player.jukeoroni.settings import Settings


class JukeBox(BaseBox):

    # box_type = 'jukebox'
    # album_type = ALBUM_TYPE_MUSIC
    # audio_dir = MUSIC_DIR

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

        self.layout = JukeboxLayout()

    @property
    def file_filter(self):
        return Settings.AUDIO_FILES

    @property
    def box_type(self):
        return 'jukebox'

    @property
    def album_type(self):
        return Settings.ALBUM_TYPE_MUSIC

    @property
    def audio_dir(self):
        return Settings.MUSIC_DIR
