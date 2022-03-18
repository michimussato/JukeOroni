import logging
import os


class Settings:
    GLOBAL_LOGGING_LEVEL = logging.DEBUG
    DJANGO_LOGGING_LEVEL = GLOBAL_LOGGING_LEVEL

    # media_crawler
    _ONE_HOUR = 3600
    DEFAULT_TRACKLIST_REGEN_INTERVAL = _ONE_HOUR * 6  # in hours
    DATA_SOURCES = ['usb_hdd', 'googledrive']
    DATA_SOURCE = DATA_SOURCES[0]  # https://raspberrytips.com/mount-usb-drive-raspberry-pi/
    DATA_SOURCE_RCLONE = DATA_SOURCES[1]
    MEDIA_ROOT = f'/data/{DATA_SOURCE}/media/audio/'
    MEDIA_ROOT_RCLONE = f'/data/{DATA_SOURCE_RCLONE}/media/audio/'
    # LOG_ROOT = os.path.join(MEDIA_ROOT, 'jukeoroni_logs')
    # if not os.path.exists(MEDIA_ROOT):
    #     DATA_SOURCE = DATA_SOURCES[1]  # Fallback to google drive if usb drive is not available
    #     MEDIA_ROOT = f'/data/{DATA_SOURCE}/media/audio/'
    ALBUM_TYPES = ['music', 'meditation', 'episodic', 'podcast']
    ALBUM_TYPE_MUSIC = ALBUM_TYPES[0]  # 'music'
    ALBUM_TYPE_MEDITATION = ALBUM_TYPES[1]  # 'meditation'
    ALBUM_TYPE_EPISODIC = ALBUM_TYPES[2]  # 'episodic'
    ALBUM_TYPE_PODCAST = ALBUM_TYPES[3]  # 'episodic'
    MUSIC_DIR = os.path.join(MEDIA_ROOT, ALBUM_TYPE_MUSIC)
    MEDITATION_DIR = os.path.join(MEDIA_ROOT, ALBUM_TYPE_MEDITATION)
    EPISODIC_DIR = os.path.join(MEDIA_ROOT, ALBUM_TYPE_EPISODIC)
    FAULTY_ALBUMS = os.path.join(MEDIA_ROOT, 'faulty_albums_test.txt')
    MISSING_COVERS_FILE = os.path.join(MEDIA_ROOT, 'missing_covers_test.txt')
    AUDIO_FILES = ['.dsf', '.flac', '.wav', '.dff']
    MEDITATION_FILTER = ['.dsf', '.flac', '.wav', '.dff']
    EPISODIC_FILES = ['.dsf', '.flac', '.wav', '.dff', '.mp3']

    # inky
    PIMORONI_SATURATION = 0.5  # Default: 0.5
    BUTTONS = [5, 6, 16, 24]

    # jukeoroni
    _OFF_IMAGE = '/data/django/jukeoroni/player/static/zzz.jpg'
    DRAW_HOST_INFO = True
    PIMORONI_WATCHER_UPDATE_INTERVAL = 1
    SMALL_WIDGET_SIZE = 160
    FFPLAY_CMD = 'ffplay -hide_banner -autoexit -vn -nodisp -loglevel error'.split(' ')

    BUTTONS_HEIGHT = 32
    BORDER = 4
    BUTTONS_ICONS = {
        'Radio': '/data/django/jukeoroni/player/static/buttons_overlay/icon_radio.png',
        'Player': '/data/django/jukeoroni/player/static/buttons_overlay/icon_player.png',
        'Meditation': '/data/django/jukeoroni/player/static/buttons_overlay/icon_meditation.png',
        'Audiobook': '/data/django/jukeoroni/player/static/buttons_overlay/icon_audiobook.png',
        'Podcast': '/data/django/jukeoroni/player/static/buttons_overlay/icon_podcast.png',
        'Random -> Album': '/data/django/jukeoroni/player/static/buttons_overlay/icon_random.png',
        'Album -> Random': '/data/django/jukeoroni/player/static/buttons_overlay/icon_album.png',
        # 'N//A': '/data/django/jukeoroni/player/static/buttons_overlay/icon_na.png',
        'N//A': '',
        'Stop': '/data/django/jukeoroni/player/static/buttons_overlay/icon_stop.png',
        'Play': '/data/django/jukeoroni/player/static/buttons_overlay/icon_play.png',
        'Next': '/data/django/jukeoroni/player/static/buttons_overlay/icon_next.png',
        'Menu': '/data/django/jukeoroni/player/static/buttons_overlay/icon_menu.png'
    }

    INVERT_BUTTONS = True
    GRADIENT_BUTTONS = True
    GRADIENT_BG = True
    GRADIENT_BG_OPACITY = 0.4
    GRADIENT_BG_BLACK_SIZE = BUTTONS_HEIGHT

    # Sync Rclone folder over to local usb hdd (make an exact copy)
    # rsync -rltv8DW --delete-before --progress --info=progress2 --dry-run --exclude "*DS_Store" --delete-excluded "/data/googledrive/media/audio/music/new/" "/data/usb_hdd/media/audio/music/new" > /data/usb_hdd/rsync_music.txt &
    RSYNC_CMD = f'rsync -rltv8DW --delete-before --progress --info=progress2 --exclude "*DS_Store" --delete-excluded "{MEDIA_ROOT_RCLONE}/{ALBUM_TYPE_MUSIC}/" "/{MEDIA_ROOT}/{ALBUM_TYPE_MUSIC}"'.split(' ')

    ENABLE_JUKEBOX = True
    ENABLE_RADIO = True
    ENABLE_MEDITATION = True
    ENABLE_PODCAST = False
    ENABLE_AUDIOBOOK = False
    ENABLE_EPISODIC = False

    STATE_WATCHER_CADENCE = 0.1  # Seconds
    STATE_WATCHER_IDLE_TIMER = 1.0  # Minutes (0.0 = off)

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
                    # '000X': ['N//A', 'Audiobook'][int(ENABLE_AUDIOBOOK)],
                    '000X': ['N//A', 'Podcast'][int(ENABLE_PODCAST)],
                    # '000X': ['N//A', 'Episodic'][int(ENABLE_EPISODIC)],
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
        # 'episodicbox': {
        #         'standby': {
        #             'random': {
        #                 'numeric': 4.0,
        #                 'name': 'episodicbox standby random',
        #                 'buttons': {
        #                     'X000': 'Menu',
        #                     '0X00': 'Play',
        #                     '00X0': 'N//A',
        #                     '000X': 'Random -> Album',
        #                 },
        #             },
        #             'album': {
        #                 'numeric': 4.1,
        #                 'name': 'episodicbox standby album',
        #                 'buttons': {
        #                     'X000': 'Menu',
        #                     '0X00': 'Play',
        #                     '00X0': 'N//A',
        #                     '000X': 'Album -> Random',
        #                 },
        #             },
        #             # 'track': {
        #             #     'numeric': 3.5,
        #             #     'name': 'meditationbox standby track',
        #             #     'buttons': {
        #             #         'X000': 'Stop',
        #             #         '0X00': 'Next',
        #             #         '00X0': 'N//A',
        #             #         '000X': 'Album -> Random',
        #             #     },
        #             # },
        #         },
        #         'on_air': {
        #             'random': {
        #                 'numeric': 4.2,
        #                 'name': 'episodicbox on_air random',
        #                 'buttons': {
        #                     'X000': 'Stop',
        #                     '0X00': 'Next',
        #                     '00X0': 'N//A',
        #                     '000X': 'Random -> Album',
        #                 },
        #             },
        #             'album': {
        #                 'numeric': 4.3,
        #                 'name': 'episodicbox on_air album',
        #                 'buttons': {
        #                     'X000': 'Stop',
        #                     '0X00': 'Next',
        #                     '00X0': 'N//A',
        #                     '000X': 'Album -> Random',
        #                 },
        #             },
        #             # 'track': {
        #             #     'numeric': 3.4,
        #             #     'name': 'meditationbox on_air album track',
        #             #     'buttons': {
        #             #         'X000': 'Stop',
        #             #         '0X00': 'Next',
        #             #         '00X0': 'N//A',
        #             #         '000X': 'Album -> Random',
        #             #     },
        #             # },
        #         },
        #     },
        'podcastbox': {
                'standby': {
                    'random': {
                        'numeric': 5.0,
                        'name': 'podcastbox standby random',
                        'buttons': {
                            'X000': 'Menu',
                            '0X00': 'Play',
                            '00X0': 'N//A',
                            '000X': 'Random -> Album',
                        },
                    },
                    'album': {
                        'numeric': 5.1,
                        'name': 'podcastbox standby album',
                        'buttons': {
                            'X000': 'Menu',
                            '0X00': 'Play',
                            '00X0': 'N//A',
                            '000X': 'Album -> Random',
                        },
                    },
                    # 'track': {
                    #     'numeric': 5.5,
                    #     'name': 'podcastbox standby track',
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
                        'numeric': 5.2,
                        'name': 'podcastbox on_air random',
                        'buttons': {
                            'X000': 'Stop',
                            '0X00': 'Next',
                            '00X0': 'N//A',
                            '000X': 'Random -> Album',
                        },
                    },
                    'album': {
                        'numeric': 5.3,
                        'name': 'podcastbox on_air album',
                        'buttons': {
                            'X000': 'Stop',
                            '0X00': 'Next',
                            '00X0': 'N//A',
                            '000X': 'Album -> Random',
                        },
                    },
                    # 'track': {
                    #     'numeric': 5.4,
                    #     'name': 'podcastbox on_air album track',
                    #     'buttons': {
                    #         'X000': 'Stop',
                    #         '0X00': 'Next',
                    #         '00X0': 'N//A',
                    #         '000X': 'Album -> Random',
                    #     },
                    # },
                },
            },
        'audiobookbox': {
                'standby': {
                    'random': {
                        'numeric': 6.0,
                        'name': 'audiobookbox standby random',
                        'buttons': {
                            'X000': 'Menu',
                            '0X00': 'Play',
                            '00X0': 'N//A',
                            '000X': 'Random -> Album',
                        },
                    },
                    'album': {
                        'numeric': 6.1,
                        'name': 'audiobookbox standby album',
                        'buttons': {
                            'X000': 'Menu',
                            '0X00': 'Play',
                            '00X0': 'N//A',
                            '000X': 'Album -> Random',
                        },
                    },
                    # 'track': {
                    #     'numeric': 6.5,
                    #     'name': 'audiobookbox standby track',
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
                        'numeric': 6.2,
                        'name': 'audiobookbox on_air random',
                        'buttons': {
                            'X000': 'Stop',
                            '0X00': 'Next',
                            '00X0': 'N//A',
                            '000X': 'Random -> Album',
                        },
                    },
                    'album': {
                        'numeric': 6.3,
                        'name': 'audiobookbox on_air album',
                        'buttons': {
                            'X000': 'Stop',
                            '0X00': 'Next',
                            '00X0': 'N//A',
                            '000X': 'Album -> Random',
                        },
                    },
                    # 'track': {
                    #     'numeric': 6.4,
                    #     'name': 'audiobookbox on_air album track',
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

    # # episodic
    # _EPISODIC_ICON_IMAGE = '/data/django/jukeoroni/player/static/episodic_box.jpg'

    # Podcast
    _PODCAST_ICON_IMAGE = '/data/django/jukeoroni/player/static/podcast_box.jpg'

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
    INVERT_RADAR = True
    ENHANCE_IMAGE = True

    # web
    RANDOM_ALBUMS = 3
