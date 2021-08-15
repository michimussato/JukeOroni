import os
from astral import LocationInfo
from PIL import Image


# media_crawler
DEFAULT_TRACKLIST_REGEN_INTERVAL = 12  # in hours
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
OFF_IMAGE = Image.open(_OFF_IMAGE).rotate(90, expand=True).resize((600, 448))
PIMORONI_WATCHER_UPDATE_INTERVAL = 5


# clock
CITY = LocationInfo("Bern", "Switzerland", "Europe/Zurich", 46.94809, 7.44744)
ANTIALIAS = 16
ARIAL = r'/data/django/jukeoroni/player/static/arial_narrow.ttf'
CALLIGRAPHIC = r'/data/django/jukeoroni/player/static/calligraphia-one.ttf'
CLOCK_UPDATE_INTERVAL = 5  # in minutes


# radar
RADAR_UPDATE_INTERVAL = 15  # in minutes
