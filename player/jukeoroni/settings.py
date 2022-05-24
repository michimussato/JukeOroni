import logging
from pathlib import Path
import os


# BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

    GLOBAL_LOGGING_LEVEL = logging.DEBUG
    DJANGO_LOGGING_LEVEL = GLOBAL_LOGGING_LEVEL

    # media_crawler
    _ONE_HOUR = 3600
    DEFAULT_TRACKLIST_REGEN_INTERVAL = _ONE_HOUR * 6  # in hours
    DATA_SOURCES = ['usb_hdd', 'googledrive']
    # rsync
    #  rsync --dry-run -rltv8DW --delete-before --progress --info=progress2 --exclude "*DS_Store" --delete-excluded "/data/googledrive/media/audio/music/" "/data/usb_hdd/media/audio/music" > /data/usb_hdd/rsync_music.txt &
    #  rsync --dry-run -rltv8DW --delete-before --progress --info=progress2 --exclude "*DS_Store" --delete-excluded "/data/googledrive/media/audio/meditation/" "/data/usb_hdd/media/audio/meditation" > /data/usb_hdd/rsync_meditation.txt &
    # Icon?
    #  find . -name 'Icon?' -exec rm {} \;
    DATA_SOURCE = DATA_SOURCES[0]  # https://raspberrytips.com/mount-usb-drive-raspberry-pi/
    DATA_SOURCE_RCLONE = DATA_SOURCES[1]
    MEDIA_ROOT = f'/data/{DATA_SOURCE}/media/audio/'
    LOG_ROOT = f'/data/jukeoroni_logs/'
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
    VIDEO_DIR = r'/data/usb_hdd/media/'
    EPISODIC_DIR = os.path.join(MEDIA_ROOT, ALBUM_TYPE_EPISODIC)
    FAULTY_ALBUMS = os.path.join(MEDIA_ROOT, 'faulty_albums_test.txt')
    MISSING_COVERS_FILE = os.path.join(MEDIA_ROOT, 'missing_covers_test.txt')
    AUDIO_FILES = ['.dsf', '.flac', '.wav', '.dff']
    MEDITATION_FILTER = ['.dsf', '.flac', '.wav', '.dff']
    VIDEO_FILTER = ['.mp4']
    EPISODIC_FILES = ['.dsf', '.flac', '.wav', '.dff', '.mp3']

    # inky
    PIMORONI_SATURATION = 0.5  # Default: 0.5
    BUTTONS = [5, 6, 16, 24]

    # jukeoroni
    _OFF_IMAGE = os.path.join(BASE_DIR, 'player', 'static', 'zzz.jpg')
    DRAW_HOST_INFO = True
    PIMORONI_WATCHER_UPDATE_INTERVAL = 1
    SMALL_WIDGET_SIZE = 160
    FFPLAY_CMD = 'ffplay -hide_banner -autoexit -vn -nodisp -loglevel error'.split(' ')
    DISABLE_TRACK_LOADER = False

    BUTTONS_HEIGHT = 32
    BORDER = 10
    BUTTONS_OVERLAY = os.path.join(BASE_DIR, 'player', 'static', 'buttons_overlay')
    BUTTONS_ICONS = {
        'Radio': os.path.join(BUTTONS_OVERLAY, 'icon_radio.png'),
        'Player': os.path.join(BUTTONS_OVERLAY, 'icon_player.png'),
        'Meditation': os.path.join(BUTTONS_OVERLAY, 'icon_meditation.png'),
        'Audiobook': os.path.join(BUTTONS_OVERLAY, 'icon_audiobook.png'),
        'Podcast': os.path.join(BUTTONS_OVERLAY, 'icon_podcast.png'),
        'Video': os.path.join(BUTTONS_OVERLAY, 'icon_video.png'),
        'Random -> Album': os.path.join(BUTTONS_OVERLAY, 'icon_random.png'),
        'Album -> Random': os.path.join(BUTTONS_OVERLAY, 'icon_album.png'),
        'N//A': '',  # use os.path.join(BUTTONS_OVERLAY, 'icon_na.png'), for debug purposes
        'Stop': os.path.join(BUTTONS_OVERLAY, 'icon_stop.png'),
        'Play': os.path.join(BUTTONS_OVERLAY, 'icon_play.png'),
        'Pause': os.path.join(BUTTONS_OVERLAY, 'icon_pause.png'),
        'Next': os.path.join(BUTTONS_OVERLAY, 'icon_next.png'),
        'Menu': os.path.join(BUTTONS_OVERLAY, 'icon_menu.png'),
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
    ENABLE_VIDEO = True

    ENABLE_TV_SCREEN_UPDATER = False
    TV_SCREEN_UPDATER_CADENCE = 5.0  # Seconds
    STATE_WATCHER_CADENCE = 0.1  # Seconds
    STATE_WATCHER_IDLE_TIMER = 15.0  # Minutes (0.0 = off)

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
                    # '000X': ['N//A', 'Podcast'][int(ENABLE_PODCAST)],
                    '000X': ['N//A', 'Video'][int(ENABLE_VIDEO)],
                    # '000X': ['N//A', 'Episodic'][int(ENABLE_EPISODIC)],
                },
            },
        },
        'radio': {
            'standby': {
                'random': {
                    'numeric': 1.0,
                    'name': 'radio standby random',
                    'buttons': {
                        'X000': 'Menu',
                        '0X00': 'Play',
                        '00X0': 'N//A',
                        '000X': 'N//A',
                    },
                },
                # Not used as the radio box only knows "random"
                'album': {
                    'numeric': 1.1,
                    'name': 'radio standby album',
                    'buttons': {
                        'X000': 'Menu',
                        '0X00': 'Play',
                        '00X0': 'N//A',
                        '000X': 'N//A',
                    },
                },
            },
            'on_air': {
                'random': {
                    'numeric': 1.2,
                    'name': 'radio on_air random',
                    'buttons': {
                        'X000': 'Stop',
                        '0X00': 'Next',
                        '00X0': 'N//A',
                        '000X': 'N//A',
                    },
                },
                # Not used as the radio box only knows "random"
                'album': {
                    'numeric': 1.3,
                    'name': 'radio on_air album',
                    'buttons': {
                        'X000': 'Stop',
                        '0X00': 'Next',
                        '00X0': 'N//A',
                        '000X': 'N//A',
                    },
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
        'videobox': {
                'standby': {
                    'random': {
                        'numeric': 7.0,
                        'name': 'videobox standby',
                        'buttons': {
                            'X000': 'Menu',
                            '0X00': 'Play',
                            '00X0': 'N//A',
                            '000X': 'N//A',
                        },
                    },
                    # 'pause': {
                    #     'numeric': 7.4,
                    #     'name': 'videobox pause',
                    #     'buttons': {
                    #         'X000': 'Stop',
                    #         '0X00': 'Play',
                    #         '00X0': 'N//A',
                    #         '000X': 'N//A',
                    #     },
                    # },
                    # Not used as the video box only knows "random"
                    'album': {
                        'numeric': 7.1,
                        'name': 'videobox standby album',
                        'buttons': {
                            'X000': 'Menu',
                            '0X00': 'Play',
                            '00X0': 'N//A',
                            '000X': 'N//A',
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
                        'numeric': 7.2,
                        'name': 'videobox on_air',
                        'buttons': {
                            'X000': 'Stop',
                            '0X00': 'Pause',
                            '00X0': 'N//A',
                            '000X': 'N//A',
                        },
                    },
                    'pause': {
                        'numeric': 7.5,
                        'name': 'videobox pause',
                        'buttons': {
                            'X000': 'Stop',
                            '0X00': 'Play',
                            '00X0': 'N//A',
                            '000X': 'N//A',
                        },
                    },
                    # Not used as the video box only knows "random"
                    'album': {
                        'numeric': 7.3,
                        'name': 'videobox on_air album',
                        'buttons': {
                            'X000': 'Stop',
                            '0X00': 'Pause',
                            '00X0': 'N//A',
                            '000X': 'N//A',
                        },
                    },
                    # 'track': {
                    #     'numeric': 6.4,
                    #     'name': 'videobox on_air album track',
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
    _JUKEBOX_ICON_IMAGE = os.path.join(BASE_DIR, 'player', 'static', 'jukebox.png')
    _JUKEBOX_LOADING_IMAGE = os.path.join(BASE_DIR, 'player', 'static', 'loading.jpg')
    _JUKEBOX_ON_AIR_DEFAULT_IMAGE = os.path.join(BASE_DIR, 'player', 'static', 'jukebox_on_air_default.jpg')

    # meditation
    _MEDITATION_ICON_IMAGE = os.path.join(BASE_DIR, 'player', 'static', 'meditation_box.jpg')

    # episodic
    _EPISODIC_ICON_IMAGE = os.path.join(BASE_DIR, 'player', 'static', 'episodic_box.jpg')

    # Podcast
    _PODCAST_ICON_IMAGE = os.path.join(BASE_DIR, 'player', 'static', 'podcast_box.jpg')

    # radio
    _RADIO_ICON_IMAGE = os.path.join(BASE_DIR, 'player', 'static', 'radio.png')
    _RADIO_ON_AIR_DEFAULT_IMAGE = os.path.join(BASE_DIR, 'player', 'static', 'radio_on_air_default.jpg')

    # video
    AUDIO_OUT = ['local', 'hdmi', 'both', 'alsa:hw:0,0'][3]
    _VIDEO_ICON_IMAGE = os.path.join(BASE_DIR, 'player', 'static', 'movie.jpg')
    _VIDEO_ON_AIR_DEFAULT_IMAGE = os.path.join(BASE_DIR, 'player', 'static', 'movie_on_air_default.jpg')

    # clock
    LAT, LONG = 47.39134, 8.85971
    TZ = "Europe/Zurich"
    ANTIALIAS = 4  # Warning: can slow down calculation drastically
    ARIAL = os.path.join(BASE_DIR, 'player', 'static', 'arial_narrow.ttf')
    CALLIGRAPHIC = os.path.join(BASE_DIR, 'player', 'static', 'calligraphia-one.ttf')
    CLOCK_UPDATE_INTERVAL = 10  # in minutes
    CLOCK_SQUARE_OPACITY = 160
    _MOON_TEXUTRE = os.path.join(BASE_DIR, 'player', 'static', 'moon_texture_small.png')

    # radar
    RADAR_UPDATE_INTERVAL = 5  # in minutes
    INVERT_RADAR = True
    ENHANCE_IMAGE = True

    # web
    RANDOM_ALBUMS = 3
