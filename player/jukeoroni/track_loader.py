import os
import time
import logging
from player.jukeoroni.settings import Settings
from player.jukeoroni.box_track import JukeboxTrack


LOG = logging.getLogger(__name__)
LOG.setLevel(Settings.GLOBAL_LOGGING_LEVEL)


def _track_loader_task(box):
    try:
        while box.on:
            try:
                LOG.debug(f'{box.box_type:<18}: {len(box.tracks)} of {Settings.MAX_CACHED_FILES} tracks cached. Queue: {box.tracks}')

                # This is to check that the source files did not disappear in the meantime
                # Remove them if they did
                box.tracks = [track for track in box.tracks if os.path.isfile(track.path)]

                if len(box.tracks) < Settings.MAX_CACHED_FILES:
                    loading_track = box.get_next_track()

                    if loading_track is None:
                        LOG.warning(f'{box.box_type:<18}: Got "None" track. Retrying...')
                        time.sleep(1.0)
                        continue
                    if not os.path.isfile(os.path.join(box.audio_dir, loading_track.audio_source)):
                        LOG.warning(
                            f'{box.box_type:<18}: Track audio_source ({os.path.join(box.audio_dir, loading_track.audio_source)}) does not exist on filesystem. Retrying...')
                        time.sleep(1.0)
                        continue

                    try:

                        LOG.info(f'{box.box_type:<18}: Next track OK: {loading_track}')

                        box.loading_track = JukeboxTrack(django_track=loading_track, cached=Settings.CACHE_TRACKS)
                        box.loading_track.cache()
                        box.loading_track.cache_online_covers()

                    except AttributeError as error:
                        LOG.exception(error)

                    finally:

                        if box.loading_track is not None:
                            if not box.loading_track.killed:
                                loading_track_copy = box.loading_track
                                box.tracks.append(loading_track_copy)
                                # TODO: make sure not to add tracks that are
                                #  already in the queue
                                # self.tracks = list(set(self.tracks))  # buggy!! Fucks up order somehow
                            box.loading_track = None

                time.sleep(1.0)
            except Exception as e:
                LOG.exception(f'{box.box_type:<18}: {e}')
                # raise e
    except Exception as e:
        LOG.exception(f'{box.box_type:<18}: {e}')
        # raise e

"""
[11-10-2022 21:44:49] [DEBUG   ] [Track Loader Thread|2898261088], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    meditationbox     : 3 of 3 tracks cached. Queue: [The Sounds Of Nature - Sparkling Springtime [FLAC][16][44.1] - 10 Sunset At Water's Edge.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 01 - First Stage_ 10 Minutes Music.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 02 - Second Stage_ 10 Minutes Music.flac]
[11-10-2022 21:44:49] [DEBUG   ] [Track Loader Thread|2919232608], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    jukebox           : 3 of 3 tracks cached. Queue: [Brothers of Metal - Emblas Saga (Japanese Edition) [FLAC][16][44.1] - 01 Brood Of The Trickster.flac, Parkway Drive - Viva The Underdogs [FLAC][16][44.1] - 05 Idols and Anchors (Live At Wacken).flac, Marilyn Manson - Eat Me, Drink Me [FLAC][16][44.1] - 03 The Red Carpet Grave.flac]
[11-10-2022 21:44:50] [DEBUG   ] [Track Loader Thread|2898261088], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    meditationbox     : 3 of 3 tracks cached. Queue: [The Sounds Of Nature - Sparkling Springtime [FLAC][16][44.1] - 10 Sunset At Water's Edge.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 01 - First Stage_ 10 Minutes Music.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 02 - Second Stage_ 10 Minutes Music.flac]
[11-10-2022 21:44:50] [DEBUG   ] [Track Loader Thread|2919232608], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    jukebox           : 3 of 3 tracks cached. Queue: [Brothers of Metal - Emblas Saga (Japanese Edition) [FLAC][16][44.1] - 01 Brood Of The Trickster.flac, Parkway Drive - Viva The Underdogs [FLAC][16][44.1] - 05 Idols and Anchors (Live At Wacken).flac, Marilyn Manson - Eat Me, Drink Me [FLAC][16][44.1] - 03 The Red Carpet Grave.flac]
[11-10-2022 21:44:51] [DEBUG   ] [Track Loader Thread|2898261088], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    meditationbox     : 3 of 3 tracks cached. Queue: [The Sounds Of Nature - Sparkling Springtime [FLAC][16][44.1] - 10 Sunset At Water's Edge.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 01 - First Stage_ 10 Minutes Music.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 02 - Second Stage_ 10 Minutes Music.flac]
[11-10-2022 21:44:51] [DEBUG   ] [Track Loader Thread|2919232608], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    jukebox           : 3 of 3 tracks cached. Queue: [Brothers of Metal - Emblas Saga (Japanese Edition) [FLAC][16][44.1] - 01 Brood Of The Trickster.flac, Parkway Drive - Viva The Underdogs [FLAC][16][44.1] - 05 Idols and Anchors (Live At Wacken).flac, Marilyn Manson - Eat Me, Drink Me [FLAC][16][44.1] - 03 The Red Carpet Grave.flac]
[11-10-2022 21:44:52] [DEBUG   ] [Track Loader Thread|2898261088], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    meditationbox     : 3 of 3 tracks cached. Queue: [The Sounds Of Nature - Sparkling Springtime [FLAC][16][44.1] - 10 Sunset At Water's Edge.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 01 - First Stage_ 10 Minutes Music.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 02 - Second Stage_ 10 Minutes Music.flac]
[11-10-2022 21:44:52] [DEBUG   ] [Track Loader Thread|2919232608], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    jukebox           : 3 of 3 tracks cached. Queue: [Brothers of Metal - Emblas Saga (Japanese Edition) [FLAC][16][44.1] - 01 Brood Of The Trickster.flac, Parkway Drive - Viva The Underdogs [FLAC][16][44.1] - 05 Idols and Anchors (Live At Wacken).flac, Marilyn Manson - Eat Me, Drink Me [FLAC][16][44.1] - 03 The Red Carpet Grave.flac]
[11-10-2022 21:44:53] [DEBUG   ] [Track Loader Thread|2898261088], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    meditationbox     : 3 of 3 tracks cached. Queue: [The Sounds Of Nature - Sparkling Springtime [FLAC][16][44.1] - 10 Sunset At Water's Edge.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 01 - First Stage_ 10 Minutes Music.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 02 - Second Stage_ 10 Minutes Music.flac]
[11-10-2022 21:44:53] [DEBUG   ] [Track Loader Thread|2919232608], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    jukebox           : 3 of 3 tracks cached. Queue: [Brothers of Metal - Emblas Saga (Japanese Edition) [FLAC][16][44.1] - 01 Brood Of The Trickster.flac, Parkway Drive - Viva The Underdogs [FLAC][16][44.1] - 05 Idols and Anchors (Live At Wacken).flac, Marilyn Manson - Eat Me, Drink Me [FLAC][16][44.1] - 03 The Red Carpet Grave.flac]
[11-10-2022 21:44:54] [DEBUG   ] [Track Loader Thread|2898261088], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    meditationbox     : 3 of 3 tracks cached. Queue: [The Sounds Of Nature - Sparkling Springtime [FLAC][16][44.1] - 10 Sunset At Water's Edge.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 01 - First Stage_ 10 Minutes Music.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 02 - Second Stage_ 10 Minutes Music.flac]
[11-10-2022 21:44:54] [DEBUG   ] [Track Loader Thread|2919232608], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    jukebox           : 2 of 3 tracks cached. Queue: [Parkway Drive - Viva The Underdogs [FLAC][16][44.1] - 05 Idols and Anchors (Live At Wacken).flac, Marilyn Manson - Eat Me, Drink Me [FLAC][16][44.1] - 03 The Red Carpet Grave.flac]
[11-10-2022 21:44:55] [DEBUG   ] [Track Loader Thread|2898261088], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    meditationbox     : 3 of 3 tracks cached. Queue: [The Sounds Of Nature - Sparkling Springtime [FLAC][16][44.1] - 10 Sunset At Water's Edge.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 01 - First Stage_ 10 Minutes Music.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 02 - Second Stage_ 10 Minutes Music.flac]
[11-10-2022 21:44:55] [INFO    ] [Track Loader Thread|2919232608], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 35, in _track_loader_task:    jukebox           : Next track OK: on_device/Volbeat - 2005 - The Strength The Sound The Songs [FLAC][16][44.1]/03 Something Else Or....flac
[11-10-2022 21:44:56] [DEBUG   ] [Track Loader Thread|2898261088], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    meditationbox     : 3 of 3 tracks cached. Queue: [The Sounds Of Nature - Sparkling Springtime [FLAC][16][44.1] - 10 Sunset At Water's Edge.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 01 - First Stage_ 10 Minutes Music.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 02 - Second Stage_ 10 Minutes Music.flac]
[11-10-2022 21:44:57] [DEBUG   ] [Track Loader Thread|2898261088], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    meditationbox     : 3 of 3 tracks cached. Queue: [The Sounds Of Nature - Sparkling Springtime [FLAC][16][44.1] - 10 Sunset At Water's Edge.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 01 - First Stage_ 10 Minutes Music.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 02 - Second Stage_ 10 Minutes Music.flac]
[11-10-2022 21:44:58] [DEBUG   ] [Track Loader Thread|2898261088], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    meditationbox     : 3 of 3 tracks cached. Queue: [The Sounds Of Nature - Sparkling Springtime [FLAC][16][44.1] - 10 Sunset At Water's Edge.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 01 - First Stage_ 10 Minutes Music.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 02 - Second Stage_ 10 Minutes Music.flac]
[11-10-2022 21:44:59] [DEBUG   ] [Track Loader Thread|2898261088], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    meditationbox     : 3 of 3 tracks cached. Queue: [The Sounds Of Nature - Sparkling Springtime [FLAC][16][44.1] - 10 Sunset At Water's Edge.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 01 - First Stage_ 10 Minutes Music.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 02 - Second Stage_ 10 Minutes Music.flac]
[11-10-2022 21:45:00] [DEBUG   ] [Track Loader Thread|2898261088], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    meditationbox     : 3 of 3 tracks cached. Queue: [The Sounds Of Nature - Sparkling Springtime [FLAC][16][44.1] - 10 Sunset At Water's Edge.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 01 - First Stage_ 10 Minutes Music.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 02 - Second Stage_ 10 Minutes Music.flac]
[11-10-2022 21:45:01] [DEBUG   ] [Track Loader Thread|2898261088], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    meditationbox     : 3 of 3 tracks cached. Queue: [The Sounds Of Nature - Sparkling Springtime [FLAC][16][44.1] - 10 Sunset At Water's Edge.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 01 - First Stage_ 10 Minutes Music.flac, Osho - Dynamic Meditation of Osho [FLAC][16][44.1] - 02 - Second Stage_ 10 Minutes Music.flac]
[11-10-2022 21:45:01] [ERROR   ] [Track Loader Thread|2919232608], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 52, in _track_loader_task:    jukebox           : 'NoneType' object has no attribute 'cache_online_covers'
Traceback (most recent call last):
  File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 39, in _track_loader_task
    box.loading_track.cache_online_covers()
AttributeError: 'NoneType' object has no attribute 'cache_online_covers'
[11-10-2022 21:45:01] [ERROR   ] [Track Loader Thread|2919232608], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 55, in _track_loader_task:    jukebox           : 'NoneType' object has no attribute 'cache_online_covers'
Traceback (most recent call last):
  File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 53, in _track_loader_task
    raise e
  File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 39, in _track_loader_task
    box.loading_track.cache_online_covers()
AttributeError: 'NoneType' object has no attribute 'cache_online_covers'

"""

"""
[11-30-2022 01:19:49] [DEBUG   ] [Track Loader Thread|2894066784], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    meditationbox     : 3 of 3 tracks cached. Queue: [David Sun - Ocean Sounds for Sensuous Massage [FLAC][16][44.1] - 01 Ocean Sounds for Sensuous Massage.flac, Jonathan Goldman - Sounds of Light [FLAC][16][44.1] - 01 - Sounds Of Light.flac, Jonathan Goldman - Sounds of Light [FLAC][16][44.1] - 02 - Tonal Alchemy.flac]
[11-30-2022 01:19:49] [DEBUG   ] [Track Loader Thread|2915038304], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    jukebox           : 3 of 3 tracks cached. Queue: [Flogging Molly - Live At The Greek Theatre (CD2) [FLAC][16][44.1] - 08 The Wrong Company.flac, Genesis - Invisible Touch [FLAC][16][44.1] - 02 Tonight, Tonight, Tonight.flac, Uriah Heep - Firefly [DSD][] - 01 The Hanging Tree.dsf]
[11-30-2022 01:19:50] [DEBUG   ] [Track Loader Thread|2894066784], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    meditationbox     : 0 of 3 tracks cached. Queue: []
[11-30-2022 01:19:50] [INFO    ] [Track Loader Thread|2894066784], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 37, in _track_loader_task:    meditationbox     : Next track OK: off_device/Calmsound - 2022 - Ocean Waves [FLAC][16][44.1]/Calmsound Ocean Waves (2 hours).flac

...

[11-30-2022 03:21:21] [ERROR   ] [Track Loader Thread|2894066784], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 59, in _track_loader_task:    meditationbox     : 'NoneType' object has no attribute 'first_album_track'
Traceback (most recent call last):
  File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 23, in _track_loader_task
    loading_track = box.get_next_track()
  File "/data/django/jukeoroni/player/jukeoroni/base_box.py", line 317, in get_next_track
    first_album_track = self.playing_track.first_album_track
AttributeError: 'NoneType' object has no attribute 'first_album_track'
[11-30-2022 03:21:21] [ERROR   ] [Track Loader Thread|2894066784], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 62, in _track_loader_task:    meditationbox     : 'NoneType' object has no attribute 'first_album_track'
Traceback (most recent call last):
  File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 60, in _track_loader_task
    raise e
  File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 23, in _track_loader_task
    loading_track = box.get_next_track()
  File "/data/django/jukeoroni/player/jukeoroni/base_box.py", line 317, in get_next_track
    first_album_track = self.playing_track.first_album_track
AttributeError: 'NoneType' object has no attribute 'first_album_track'
"""
