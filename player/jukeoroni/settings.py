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
            'buttons': {
                'X000': 'N//A',
                '0X00': 'N//A',
                '00X0': 'N//A',
                '000X': 'ON',  # TODO: ON is not working yet
            }
        },
        'standby': {
            'numeric': 1.0,
            'buttons': {
                'X000': 'Player',
                '0X00': 'Radio',
                '00X0': 'N//A',
                '000X': 'N//A',  # TODO cannot switch it back on after OFF
            }
        }
    },
    'radio': {
        'standby': {
            'numeric': 1.0,
            'buttons': {
                'X000': 'Back',
                '0X00': 'Play',
                '00X0': 'N//A',
                '000X': 'N//A',
            }
        },
        'on_air': {
            'numeric': 1.1,
            'buttons': {
                'X000': 'Stop',
                '0X00': 'Next',
                '00X0': 'N//A',
                '000X': 'N//A',
            }
        }
    },
    'jukebox': {
        'standby_random': {
            'numeric': 2.0,
            'buttons': {
                'X000': 'Back',
                '0X00': 'Play',
                '00X0': 'N//A',
                '000X': 'Random -> Album',
            }
        },
        'standby_album': {
            'numeric': 2.1,
            'buttons': {
                'X000': 'Back',
                '0X00': 'Play',
                '00X0': 'N//A',
                '000X': 'Random -> Album',
            }
        },
        'on_air_random': {
            'numeric': 2.2,
            'buttons': {
                'X000': 'Stop',
                '0X00': 'Next',
                '00X0': 'N//A',
                '000X': 'Random -> Album',
            }
        },
        'on_air_album': {
            'numeric': 2.3,
            'buttons': {
                'X000': 'Stop',
                '0X00': 'Next',
                '00X0': 'N//A',
                '000X': 'Album -> Random',
            }
        }
    },
}


# box
MAX_CACHED_FILES = 3
COVER_ONLINE_PREFERENCE = False
# AUDIO_FILES = ['.dsf', '.flac', '.wav', '.dff']
# DEFAULT_TRACKLIST_REGEN_INTERVAL = 12  # in hours


# radio
_RADIO_ICON_IMAGE = '/data/django/jukeoroni/player/static/radio.png'
_ON_AIR_DEFAULT_IMAGE = '/data/django/jukeoroni/player/static/radio_on_air_default.jpg'


# clock
CITY = LocationInfo("Bern", "Switzerland", "Europe/Zurich", 46.94809, 7.44744)
ANTIALIAS = 16
ARIAL = r'/data/django/jukeoroni/player/static/arial_narrow.ttf'
CALLIGRAPHIC = r'/data/django/jukeoroni/player/static/calligraphia-one.ttf'
CLOCK_UPDATE_INTERVAL = 5  # in minutes


# radar
RADAR_UPDATE_INTERVAL = 15  # in minutes
