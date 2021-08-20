import io
import random
import logging
import urllib.request
from PIL import Image
from player.jukeoroni.displays import Radio as RadioLayout
from player.jukeoroni.is_string_url import is_string_an_url
from player.models import Channel
from player.jukeoroni.settings import (
    ON_AIR_DEFAULT_IMAGE,
    GLOBAL_LOGGING_LEVEL,
    RADIO_ICON_IMAGE,
)


LOG = logging.getLogger(__name__)
LOG.setLevel(GLOBAL_LOGGING_LEVEL)


class Radio(object):
    def __init__(self):

        self.layout = RadioLayout()
        self.is_on_air = None
        self.playback_proc = None

    @property
    def cover(self):
        cover = None
        if isinstance(self.is_on_air, Channel):
            cover = self.is_on_air.url_logo
            if cover is None:
                cover = ON_AIR_DEFAULT_IMAGE
            elif is_string_an_url(cover):
                try:
                    hdr = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}
                    req = urllib.request.Request(cover, headers=hdr)
                    response = urllib.request.urlopen(req)
                    if response.status == 200:
                        cover = io.BytesIO(response.read())
                        cover = Image.open(cover)
                except Exception as err:
                    LOG.exception(f'Could not get online cover:')
                    cover = ON_AIR_DEFAULT_IMAGE

            else:
                cover = Image.open(cover).resize((448, 448))
        elif self.is_on_air is None:
            cover = RADIO_ICON_IMAGE

        if cover is None:
            raise TypeError('Channel cover is None')

        return cover

    @property
    def button_X000_value(self):
        if self.is_on_air:
            return 'Stop'
        elif not self.is_on_air:
            return 'Back'

    @property
    def button_0X00_value(self):
        if self.is_on_air:
            return 'Next'
        elif not self.is_on_air:
            return 'Play'

    @property
    def button_00X0_value(self):
        if self.is_on_air:
            return '00X0'
        elif not self.is_on_air:
            return '00X0'

    @property
    def button_000X_value(self):
        if self.is_on_air:
            return '000X'
        elif not self.is_on_air:
            return '000X'

    @property
    def channels(self):
        return Channel.objects.all()

    @staticmethod
    def get_channels_by_kwargs(**kwargs):
        # i.e. self.get_channels_by_kwargs(display_name_short='srf_swiss_pop')[0])
        return Channel.objects.filter(**kwargs)

    @property
    def random_channel(self):
        return random.choice(self.channels)

    @property
    def last_played(self):
        return Channel.objects.get(last_played=True)