import io
import random
import logging
import urllib.request
from PIL import Image
from player.jukeoroni.displays import Radio as RadioLayout
from player.jukeoroni.is_string_url import is_string_url
from player.models import Channel
from player.jukeoroni.settings import (
    GLOBAL_LOGGING_LEVEL,
    # MODES,
)
from player.jukeoroni.images import Resource


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
                cover = Resource().squareify(Resource().RADIO_ON_AIR_DEFAULT_IMAGE)
            elif is_string_url(cover):
                try:
                    hdr = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}
                    req = urllib.request.Request(cover, headers=hdr)
                    response = urllib.request.urlopen(req)
                    if response.status == 200:
                        cover = io.BytesIO(response.read())
                        cover = Image.open(cover)
                except Exception as err:
                    LOG.exception(f'Could not get online cover:')
                    cover = Resource().ON_AIR_DEFAULT_IMAGE_SQUARE

            else:
                cover = Image.open(cover).resize((448, 448))
        elif self.is_on_air is None:
            cover = Resource().RADIO_ICON_IMAGE_SQUARE

        if cover is None:
            raise TypeError('Channel cover is None')

        return cover

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
        try:
            return Channel.objects.get(last_played=True)
        except Channel.DoesNotExist:
            LOG.exception('last_played not found:')
            return None
