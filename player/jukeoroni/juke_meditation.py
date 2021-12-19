import logging

from player.jukeoroni.juke_box import JukeboxTrack
from player.jukeoroni.displays import Meditationbox as MeditationboxLayout
from player.jukeoroni.settings import (
    GLOBAL_LOGGING_LEVEL,
)

LOG = logging.getLogger(__name__)
LOG.setLevel(GLOBAL_LOGGING_LEVEL)


class MeditationTrack(JukeboxTrack):
    def __init__(self, django_track, cached=True):
        super(MeditationTrack, self).__init__(django_track, cached)


class Meditationbox(object):

    def __init__(self, jukeoroni=None):

        self.on = False
        self.loader_mode = 'album'

        self.jukeoroni = jukeoroni
        if self.jukeoroni is None:
            LOG.warning('No jukeoroni specified. Functionality is limited.')

        self.layout = MeditationboxLayout()
