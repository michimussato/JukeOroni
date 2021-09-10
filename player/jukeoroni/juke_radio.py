import io
import random
import logging
import threading
import time
import urllib.request
from PIL import Image
from pydub.utils import mediainfo
from player.jukeoroni.displays import Radio as RadioLayout
from player.jukeoroni.is_string_url import is_string_url
from player.models import Channel
from player.jukeoroni.images import Resource
from player.jukeoroni.settings import (
    GLOBAL_LOGGING_LEVEL,
)


LOG = logging.getLogger(__name__)
LOG.setLevel(GLOBAL_LOGGING_LEVEL)


class Radio(object):
    def __init__(self):

        self.layout = RadioLayout()
        self.is_on_air = None
        self.playback_proc = None
        self._media_info = None
        self._media_info_previous = None
        self._media_info_thread = None

        self.media_info_updater_thread()

    @property
    def media_info(self):
        return self._media_info

    @property
    def stream_name(self):
        if self.media_info is not None:
            return self.media_info['TAG']['icy-name']
        else:
            return None

    @property
    def stream_title(self):
        if self.media_info is not None:
            return self.media_info['TAG']['StreamTitle']
        else:
            return None

    def media_info_updater_thread(self):
        self._media_info_thread = threading.Thread(target=self.media_info_updater_task)
        self._media_info_thread.name = 'Stream Info Thread'
        self._media_info_thread.daemon = False
        self._media_info_thread.start()

    def media_info_updater_task(self):
        while self.is_on_air is not None:
            LOG.info('Updating stream info...')
            self._media_info = mediainfo(self.is_on_air.url)
            if self._media_info != self._media_info_previous:
                self._media_info_previous = self._media_info
            LOG.info('Stream info updated.')
            time.sleep(20.0)
        self._media_info = None

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
                except Exception:
                    LOG.exception(f'Could not get online cover:')
                    cover = Resource().ON_AIR_DEFAULT_IMAGE_SQUARE

            else:
                cover = Image.open(cover).resize((448, 448))
        elif self.is_on_air is None:
            cover = Resource().RADIO_ICON_IMAGE_SQUARE

        if cover is None:
            raise TypeError('Channel cover is None')

        if cover.mode == 'RGB':
            a_channel = Image.new('L', cover.size, 255)
            cover.putalpha(a_channel)
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
