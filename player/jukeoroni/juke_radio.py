import io
import random
import logging
import threading
import time
import urllib.request
from PIL import ImageFile, Image
from pydub.utils import mediainfo
from player.jukeoroni.displays import Radio as RadioLayout
from player.jukeoroni.is_string_url import is_string_url
from player.jukeoroni.key_from_nested_dict import find_by_key
from player.models import Channel
from player.jukeoroni.images import Resource
from player.jukeoroni.settings import Settings


LOG = logging.getLogger(__name__)
LOG.setLevel(Settings.GLOBAL_LOGGING_LEVEL)


ImageFile.LOAD_TRUNCATED_IMAGES = True


class Radio(object):
    def __init__(self):

        self.layout = RadioLayout()
        self.is_on_air = None
        self.playback_proc = None
        self._media_info = {}
        self._media_info_previous = {}
        self._media_info_thread = None
        self.loader_mode = 'random'

    @property
    def box_type(self):
        return 'radio'

    @property
    def media_info(self):
        return self._media_info

    @property
    def tag(self):
        tag = find_by_key(self.media_info, 'TAG')
        return tag

    @property
    def stream_name(self):
        if bool(self.tag):
            return self.tag.get('icy-name', None)
        else:
            return None

    @property
    def stream_title(self):
        if bool(self.tag) and self.is_on_air is not None:
            # get the settings of a channel from the db to reflect up-to-date data
            on_air_channel = self.get_channels_by_kwargs(display_name_short=self.is_on_air.display_name_short)[0]
            if on_air_channel.show_rds:
                return self.tag.get('StreamTitle', None)
            else:
                return None
        else:
            return None

    # @property
    # def title(self):
    #     return self.stream_title

    def media_info_updater_thread(self, channel):
        self._media_info_thread = threading.Thread(target=self.media_info_updater_task, kwargs={'Channel': channel})
        self._media_info_thread.name = 'Stream Info Thread'
        self._media_info_thread.daemon = False
        self._media_info_thread.start()

    def media_info_updater_task(self, **kwargs):
        channel = kwargs['Channel']
        while channel == self.is_on_air:
            LOG.info('Updating stream info...')
            self._media_info = mediainfo(self.is_on_air.url)
            LOG.info('Stream info updated.')
            time.sleep(20.0)
        LOG.info(f'Channel was changed, thread loop for channel {channel} terminated.')
        self._media_info = {}

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

        if cover.mode != 'RGBA':
            cover = cover.convert('RGBA')

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
            # LOG.exception('no last_played channel, returning random.')
            LOG.info('no last_played channel, returning None.')
            return None
