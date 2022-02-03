import logging
import xml.etree.ElementTree as ET
import urllib.request
import datetime
import uuid
from player.jukeoroni.base_box import BaseBox
from player.jukeoroni.displays import Podcastbox as PodcastboxLayout
from player.jukeoroni.settings import Settings


class PodcastBox(BaseBox):
    """
from player.jukeoroni.podcast_box import PodcastBox
box = PodcastBox()
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

        self.layout = PodcastboxLayout()

    @property
    def box_type(self):
        return 'podcastbox'

    @property
    def album_type(self):
        return Settings.ALBUM_TYPE_PODCAST

    @property
    def audio_dir(self):
        return

    def turn_on(self, disable_track_loader=False):
        assert not self.on, f'{self.box_type} is already on.'

        # self.temp_cleanup()

        self.on = True

        # self.track_list_generator_thread()
        # if not disable_track_loader:
        #     self.track_loader_thread()
        # # self.track_loader_watcher_thread()

        # self.parse_xml_from_url()

    def podcasts(self):
        return list()

    def parse_xml_from_url(self, url):
        """
from player.jukeoroni.podcast_box import PodcastBox
box = PodcastBox()
episodes = box.parse_xml_from_url('https://www.srf.ch/feed/podcast/sd/36f8805d-77d7-4940-a028-0b16c9808756.xml')
episodes_feedburner = box.parse_xml_from_url('https://feeds.feedburner.com/tedtalks_video')

        Returns:

        """

        # FeedBurner: https://stackoverflow.com/questions/4687042/getting-raw-xml-data-from-a-feedburner-rss-feed

        # https://stackoverflow.com/questions/54764528/how-to-read-xml-file-from-url-in-python
        # url = 'https://www.srf.ch/feed/podcast/sd/36f8805d-77d7-4940-a028-0b16c9808756.xml'
        response = urllib.request.urlopen(url).read()
        tree = ET.fromstring(response)
        # root = tree.getroot()

        self.LOG.debug(f'Parsing Podcast XML URL: {url}')

        title_channel = tree.find('.//channel/title')

        namespaces = {
            'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd',
            'atom': 'http://www.w3.org/2005/Atom'
        }
        author_channel = tree.find('.//channel/itunes:author', namespaces=namespaces)
        # print(author_channel.text)
        image = tree.find('.//image/url')
        image_url = image.text

        episodes = tree.findall('.//item')
        self.LOG.debug(f'Podcast "{title_channel.text}" (by "{author_channel.text}") has {len(episodes)} episodes.')

        # print(episodes)

        _episodes = []
        _episode = {}

        for episode in episodes:
            # print(dir(episode))
            title_episode = episode.find('title')
            author_episode = episode.find('author')
            guid = episode.find('guid')
            pub_date = episode.find('pubDate')
            enclosure = episode.find('enclosure')
            duration = episode.find('itunes:duration', namespaces=namespaces)
            # print(title_episode.tag)  # title
            # print(title.attrib)  # {}
            # print(title_episode.text)  # Dark Social 2: Telegram - Königin der Dunkelheit
            _episode['title'] = title_episode.text
            _episode['author'] = author_episode.text
            _episode['author_channel'] = author_channel.text
            # _episode['duration'] = int(duration.text)
            _episode['duration'] = duration.text
            _episode['pub_date'] = datetime.datetime.strptime(pub_date.text, '%a, %d %b %Y %H:%M:%S %z')

            # print(dir(title_episode))
            # print(guid.text)  # c802f10b-9375-4562-ad23-e3fbb930d0ff
            # _episode['guid'] = uuid.UUID(guid.text)
            _episode['guid'] = guid.text
            # print(enclosure.text)  # None
            # print(enclosure.tag)  # enclosure
            # print(enclosure.attrib)  # {'type': 'audio/mpeg', 'length': '48734055', 'url': 'https://podcasts.srf.ch/world/audio/Hotspot_02-02-2022-0602.1643718239686.mp3?assetId=c802f10b-9375-4562-ad23-e3fbb930d0ff'}
            _episode['attrib'] = enclosure.attrib
            # print(enclosure.tail)  # None

            # itunes = episode.find('itunes:duration')
            # print(itunes)
            # print(itunes.text)
            # print(itunes.tag)
            # print(itunes.tail)
            # print(itunes.attrib)

            # print(_episode)

            _episodes.append(_episode.copy())

            # break

        # print(title_channel.text)
        # print(image.text)

        # for i in _episodes:
        #     print(i)

        return _episodes