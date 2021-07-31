import os
import shutil
import tempfile
import logging
import multiprocessing
from pydub.utils import mediainfo
from player.models import Album


LOG = logging.getLogger(__name__)


class JukeTrack(object):
    def __init__(self, track, cached=True):
        self.track = track
        self.path = self.track.audio_source
        self.cached = cached
        self.cache = None
        self.is_playing = False

        if self.cached:
            self._cache()

    @property
    def cover(self):
        album = Album.objects.get(track=self.track)
        return album.cover

    @property
    def media_info(self):
        return mediainfo(self.path)

    def _cache(self):
        self.cache = tempfile.mkstemp()[1]
        logging.info(f'copying to local filesystem: \"{self.path}\" as \"{self.cache}\"')
        print(f'copying to local filesystem: \"{self.path}\" as \"{self.cache}\"')
        shutil.copy(self.path, self.cache)

    @property
    def playing_from(self):
        return self.cache if self.cached else self.path

    def play(self):
        try:
            # ffplay -threads
            logging.info(f'starting playback: \"{self.path}\" from: \"{self.playing_from}\"')
            print(f'starting playback: \"{self.path}\" from: \"{self.playing_from}\"')
            self.track.played += 1
            self.track.save()
            self.is_playing = True
            print(multiprocessing.current_process().pid)
            # TODO: now this would be a classic
            #  subprocess example: calling an external
            #  application
            # TODO: or use python-ffmpeg??
            os.system(f'ffplay -hide_banner -autoexit -vn -nodisp -loglevel error \"{self.playing_from}\"')
            logging.info(f'playback finished: \"{self.path}\"')
            print(f'playback finished: \"{self.path}\"')
        except Exception as err:
            print(err)
            logging.exception('playback failed: \"{0}\"'.format(self.path))
            print('playback failed: \"{0}\"'.format(self.path))
        finally:
            self.is_playing = False
            if self.cached:
                os.remove(self.cache)
                logging.info(f'removed from local filesystem: \"{self.cache}\"')
                print(f'removed from local filesystem: \"{self.cache}\"')

    # # this would be easiest for cleanup, but the way multiprocessing seems to hand
    # # over objects, this method is not working anymore
    # def __del__(self):
    #     if self.cache is not None:
    #         try:
    #             os.remove(self.cache)
    #             logging.info('removed from local filesystem: \"{0}\"'.format(self.cache))
    #             print('removed from local filesystem: \"{0}\"'.format(self.cache))
    #         except Exception:
    #             logging.exception('deletion failed: \"{0}\"'.format(self.cache))
    #     else:
    #         pass