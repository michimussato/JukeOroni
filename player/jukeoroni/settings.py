import logging
import os
from astral import LocationInfo


GLOBAL_LOGGING_LEVEL = logging.INFO


LOG = logging.getLogger(__name__)
LOG.setLevel(GLOBAL_LOGGING_LEVEL)


# media_crawler
DEFAULT_TRACKLIST_REGEN_INTERVAL = 3600 * 12  # in hours
MEDIA_ROOT = r'/data/googledrive/media/audio/'
MUSIC_DIR = os.path.join(MEDIA_ROOT, 'music')
FAULTY_ALBUMS = os.path.join(MEDIA_ROOT, 'faulty_albums_test.txt')
MISSING_COVERS_FILE = os.path.join(MEDIA_ROOT, 'missing_covers_test.txt')
AUDIO_FILES = ['.dsf', '.flac', '.wav', '.dff']


# inky
PIMORONI_SATURATION = 1.0
BUTTONS = [5, 6, 16, 24]

# jukeoroni
_OFF_IMAGE = '/data/django/jukeoroni/player/static/zzz.jpg'
PIMORONI_WATCHER_UPDATE_INTERVAL = 5
SMALL_WIDGET_SIZE = 150
FFPLAY_CMD = 'ffplay -hide_banner -autoexit -vn -nodisp -loglevel error'.split(' ')

_BUTTON_MAPPINGS = ['000X', '00X0', '0X00', 'X000']

MODES = {
    'jukeoroni': {
        'off': {
            'numeric': 0.0,
            'name': 'off',
            'buttons': {
                'X000': 'N//A',
                '0X00': 'N//A',
                '00X0': 'N//A',
                '000X': 'ON',  # TODO: ON is not working yet
            },
        },
        'standby': {
            'numeric': 1.0,
            'name': 'standby',
            'buttons': {
                'X000': 'Player',
                '0X00': 'Radio',
                '00X0': 'N//A',
                '000X': 'N//A',  # TODO cannot switch it back on after OFF
            },
        },
    },
    'radio': {
        'standby': {
            'numeric': 1.0,
            'name': 'radio standby',
            'buttons': {
                'X000': 'Menu',
                '0X00': 'Play',
                '00X0': 'N//A',
                '000X': 'N//A',
            },
        },
        'on_air': {
            'numeric': 1.1,
            'name': 'radio on_air',
            'buttons': {
                'X000': 'Stop',
                '0X00': 'Next',
                '00X0': 'N//A',
                '000X': 'N//A',
            },
        },
    },
    'jukebox': {
        'standby': {
            'random': {
                'numeric': 2.0,
                'name': 'jukebox standby random',
                'buttons': {
                    'X000': 'Menu',
                    '0X00': 'Play',
                    '00X0': 'N//A',
                    '000X': 'Random -> Album',
                },
            },
            'album': {
                'numeric': 2.1,
                'name': 'jukebox standby album',
                'buttons': {
                    'X000': 'Menu',
                    '0X00': 'Play',
                    '00X0': 'N//A',
                    '000X': 'Album -> Random',
                },
            },
        },
        'on_air': {
            'random': {
                'numeric': 2.2,
                'name': 'jukebox on_air random',
                'buttons': {
                    'X000': 'Stop',
                    '0X00': 'Next',
                    '00X0': 'N//A',
                    '000X': 'Random -> Album',
                },
            },
            'album': {
                'numeric': 2.3,
                'name': 'jukebox on_air album',
                'buttons': {
                    'X000': 'Stop',
                    '0X00': 'Next',
                    '00X0': 'N//A',
                    '000X': 'Album -> Random',
                },
            },
        },
    },
}


# box
MAX_CACHED_FILES = 3
COVER_ONLINE_PREFERENCE = False
_JUKEBOX_ICON_IMAGE = '/data/django/jukeoroni/player/static/jukebox.png'
_JUKEBOX_LOADING_IMAGE = '/data/django/jukeoroni/player/static/loading.jpg'
_JUKEBOX_ON_AIR_DEFAULT_IMAGE = '/data/django/jukeoroni/player/static/jukebox_on_air_default.jpg'
# AUDIO_FILES = ['.dsf', '.flac', '.wav', '.dff']
# DEFAULT_TRACKLIST_REGEN_INTERVAL = 12  # in hours


# radio
_RADIO_ICON_IMAGE = '/data/django/jukeoroni/player/static/radio.png'
_RADIO_ON_AIR_DEFAULT_IMAGE = '/data/django/jukeoroni/player/static/radio_on_air_default.jpg'


# clock
CITY = LocationInfo("Bern", "Switzerland", "Europe/Zurich", 46.94809, 7.44744)
ANTIALIAS = 16
ARIAL = r'/data/django/jukeoroni/player/static/arial_narrow.ttf'
CALLIGRAPHIC = r'/data/django/jukeoroni/player/static/calligraphia-one.ttf'
CLOCK_UPDATE_INTERVAL = 5  # in minutes


# radar
RADAR_UPDATE_INTERVAL = 15  # in minutes
