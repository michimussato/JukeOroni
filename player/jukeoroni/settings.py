import logging
import os


GLOBAL_LOGGING_LEVEL = logging.DEBUG


LOG = logging.getLogger(__name__)
LOG.setLevel(GLOBAL_LOGGING_LEVEL)


# media_crawler
_ONE_HOUR = 3600
DEFAULT_TRACKLIST_REGEN_INTERVAL = _ONE_HOUR * 6  # in hours
DATA_SOURCES = ['usb_hdd', 'googledrive']
DATA_SOURCE = DATA_SOURCES[0]  # https://raspberrytips.com/mount-usb-drive-raspberry-pi/
MEDIA_ROOT = f'/data/{DATA_SOURCE}/media/audio/'
# if not os.path.exists(MEDIA_ROOT):
#     DATA_SOURCE = DATA_SOURCES[1]  # Fallback to google drive if usb drive is not available
#     MEDIA_ROOT = f'/data/{DATA_SOURCE}/media/audio/'
ALBUM_TYPE_MUSIC = 'music'
ALBUM_TYPE_MEDITATION = 'meditation'
ALBUM_TYPE_AUDIOBOOKS = 'audiobooks'
MUSIC_DIR = os.path.join(MEDIA_ROOT, ALBUM_TYPE_MUSIC)
MEDITATION_DIR = os.path.join(MEDIA_ROOT, ALBUM_TYPE_MEDITATION)
FAULTY_ALBUMS = os.path.join(MEDIA_ROOT, 'faulty_albums_test.txt')
MISSING_COVERS_FILE = os.path.join(MEDIA_ROOT, 'missing_covers_test.txt')
AUDIO_FILES = ['.dsf', '.flac', '.wav', '.dff']


# inky
PIMORONI_SATURATION = 0.5  # Default: 0.5
BUTTONS = [5, 6, 16, 24]

# jukeoroni
_OFF_IMAGE = '/data/django/jukeoroni/player/static/zzz.jpg'
DRAW_HOST_INFO = True
PIMORONI_WATCHER_UPDATE_INTERVAL = 1
SMALL_WIDGET_SIZE = 160
FFPLAY_CMD = 'ffplay -hide_banner -autoexit -vn -nodisp -loglevel error'.split(' ')

ENABLE_JUKEBOX = True
ENABLE_RADIO = True
ENABLE_MEDITATION = True

STATE_WATCHER_CADENCE = 0.5

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
                # 'X000': 'N//A',  # means that it will have no icon
                'X000': ['N//A', 'Player'][int(ENABLE_JUKEBOX)],
                '0X00': ['N//A', 'Radio'][int(ENABLE_RADIO)],
                '00X0': ['N//A', 'Meditation'][int(ENABLE_MEDITATION)],
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
            # 'track': {
            #     'numeric': 2.5,
            #     'name': 'jukebox standby track',
            #     'buttons': {
            #         'X000': 'Stop',
            #         '0X00': 'Next',
            #         '00X0': 'N//A',
            #         '000X': 'Album -> Random',
            #     },
            # },
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
            # 'track': {
            #     'numeric': 2.4,
            #     'name': 'jukebox on_air album track',
            #     'buttons': {
            #         'X000': 'Stop',
            #         '0X00': 'Next',
            #         '00X0': 'N//A',
            #         '000X': 'Album -> Random',
            #     },
            # },
        },
    },
    'meditationbox': {
            'standby': {
                'random': {
                    'numeric': 3.0,
                    'name': 'meditationbox standby random',
                    'buttons': {
                        'X000': 'Menu',
                        '0X00': 'Play',
                        '00X0': 'N//A',
                        '000X': 'Random -> Album',
                    },
                },
                'album': {
                    'numeric': 3.1,
                    'name': 'meditationbox standby album',
                    'buttons': {
                        'X000': 'Menu',
                        '0X00': 'Play',
                        '00X0': 'N//A',
                        '000X': 'Album -> Random',
                    },
                },
                # 'track': {
                #     'numeric': 3.5,
                #     'name': 'meditationbox standby track',
                #     'buttons': {
                #         'X000': 'Stop',
                #         '0X00': 'Next',
                #         '00X0': 'N//A',
                #         '000X': 'Album -> Random',
                #     },
                # },
            },
            'on_air': {
                'random': {
                    'numeric': 3.2,
                    'name': 'meditationbox on_air random',
                    'buttons': {
                        'X000': 'Stop',
                        '0X00': 'Next',
                        '00X0': 'N//A',
                        '000X': 'Random -> Album',
                    },
                },
                'album': {
                    'numeric': 3.3,
                    'name': 'meditationbox on_air album',
                    'buttons': {
                        'X000': 'Stop',
                        '0X00': 'Next',
                        '00X0': 'N//A',
                        '000X': 'Album -> Random',
                    },
                },
                # 'track': {
                #     'numeric': 3.4,
                #     'name': 'meditationbox on_air album track',
                #     'buttons': {
                #         'X000': 'Stop',
                #         '0X00': 'Next',
                #         '00X0': 'N//A',
                #         '000X': 'Album -> Random',
                #     },
                # },
            },
        },
}


# box
CACHE_TRACKS = [True, False][1] if DATA_SOURCE == DATA_SOURCES[0] else [True, False][0]
CACHE_COVERS = [True, False][0]
MAX_CACHED_FILES = 3
COVER_ONLINE_PREFERENCE = [True, False][1]
_JUKEBOX_ICON_IMAGE = '/data/django/jukeoroni/player/static/jukebox.png'
_JUKEBOX_LOADING_IMAGE = '/data/django/jukeoroni/player/static/loading.jpg'
_JUKEBOX_ON_AIR_DEFAULT_IMAGE = '/data/django/jukeoroni/player/static/jukebox_on_air_default.jpg'
# AUDIO_FILES = ['.dsf', '.flac', '.wav', '.dff']
# DEFAULT_TRACKLIST_REGEN_INTERVAL = 12  # in hours


# meditation
_MEDITATION_ICON_IMAGE = '/data/django/jukeoroni/player/static/meditation_box.jpg'

# radio
_RADIO_ICON_IMAGE = '/data/django/jukeoroni/player/static/radio.png'
_RADIO_ON_AIR_DEFAULT_IMAGE = '/data/django/jukeoroni/player/static/radio_on_air_default.jpg'


# clock
LAT, LONG = 47.39134, 8.85971
TZ = "Europe/Zurich"
ANTIALIAS = 4  # Warning: can slow down calculation drastically
ARIAL = r'/data/django/jukeoroni/player/static/arial_narrow.ttf'
CALLIGRAPHIC = r'/data/django/jukeoroni/player/static/calligraphia-one.ttf'
CLOCK_UPDATE_INTERVAL = 10  # in minutes
_MOON_TEXUTRE = '/data/django/jukeoroni/player/static/moon_texture_small.png'


# radar
RADAR_UPDATE_INTERVAL = 5  # in minutes


# web
RANDOM_ALBUMS = 3
