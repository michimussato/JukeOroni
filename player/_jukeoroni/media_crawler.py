import os
import time
import multiprocessing
import logging
from player.jukeoroni.settings import DEFAULT_TRACKLIST_REGEN_INTERVAL
from player.jukeoroni.settings import MUSIC_DIR
from player.jukeoroni.settings import FAULTY_ALBUMS
from player.jukeoroni.settings import MISSING_COVERS_FILE
from player.jukeoroni.settings import AUDIO_FILES
from player.models import Artist
from player.models import Album
from player.models import Track


LOG = logging.getLogger(__name__)


class MediaCrawlerException(Exception):
    pass


class MediaCrawler(object):
    def __init__(self):
        self.auto_update_tracklist = False

        # # https://stackoverflow.com/questions/32053618/how-to-to-terminate-process-using-pythons-multiprocessing
        # self.queue = multiprocessing.Queue()

        self._track_list_generator_thread = None
        self._track_loader_thread = None

    def turn_on(self):
        pass

    def shut_down(self):
        pass

    @property
    def pid(self):
        if self._track_list_generator_thread is None:
            raise MediaCrawlerException('Process was not created yet')
        if self._track_list_generator_thread.is_alive():
            return self._track_list_generator_thread.pid
        else:
            return None

    ############################################
    # track list generator process
    def track_list_generator_worker(self, **kwargs):
        self._track_list_generator_thread = multiprocessing.Process(target=self.track_list_generator_task, kwargs=kwargs)
        self._track_list_generator_thread.name = 'Track List Generator Process'
        self._track_list_generator_thread.daemon = True
        self._track_list_generator_thread.start()

    def track_list_generator_task(self, **kwargs):
        while True:
            if self.auto_update_tracklist:
                self.create_update_track_list()
            # instead of putting it to sleep, we
            # could schedule it (so that it can finish an
            # restart at some given time again)
            time.sleep(kwargs.get('auto_update_tracklist_interval') or DEFAULT_TRACKLIST_REGEN_INTERVAL/3600)  # is 12 hours

    @staticmethod
    def create_update_track_list():
        # TODO: filter image files, m3u etc.
        logging.info('generating updated track list...')
        print('generating updated track list...')
        _files = []
        for path, dirs, files in os.walk(MUSIC_DIR):
            album = os.path.basename(path)
            try:
                # TODO: maybe use a better character
                artist, year, title = album.split(' - ')
            except ValueError as err:
                with open(FAULTY_ALBUMS, 'a+') as f:
                    f.write(album + '\n')
                # TODO: store this somewhere to fix it
                print(err)
                LOG.exception(f'not a valid album path: {album}')
                print(f'not a valid album path: {album}')
                continue

            query_artist = Artist.objects.filter(name__exact=artist)
            if bool(query_artist):
                model_artist = query_artist[0]
                # print('    artist found in db')
            else:
                model_artist = Artist(name=artist)
                model_artist.save()
                # print('    artist created in db')

            cover_root = path
            jpg_path = os.path.join(cover_root, 'cover.jpg')
            png_path = os.path.join(cover_root, 'cover.png')
            if os.path.exists(jpg_path):
                img_path = jpg_path
            elif os.path.exists(png_path):
                img_path = png_path
            else:
                with open(MISSING_COVERS_FILE, 'a+') as f:
                    f.write(cover_root + '\n')
                logging.info(f'cover is None: {album}')
                print(f'cover is None: {album}')
                img_path = None

            # need to add artist too
            query_album = Album.objects.filter(artist_id=model_artist, album_title__exact=title, year__exact=year)

            if bool(query_album):
                model_album = query_album[0]
                model_album.cover = img_path
                # print('    album found in db')
            else:
                model_album = Album(artist_id=model_artist, album_title=title, year=year, cover=img_path)
                # print('    album created in db')

            try:
                model_album.save()
            except Exception as err:
                logging.exception(err)
                print(err)

            for _file in files:
                # print('      track: ' + _file)
                if os.path.splitext(_file)[1] in AUDIO_FILES:
                    file_path = os.path.join(path, _file)
                    query_track = Track.objects.filter(audio_source__exact=file_path)

                    # # TODO: will throw error if query returns zero or more than one
                    # #  result
                    # query_track = DjangoTrack.objects.get(audio_source__exact=file_path)

                    if not bool(query_track):
                        model_track = Track(album_id=model_album, audio_source=file_path)
                        model_track.save()
                        # print('        track created in db')

                    _files.append(file_path)

        # remove obsolete db objects:
        django_tracks = Track.objects.all()
        for django_track in django_tracks:
            if django_track.audio_source not in _files:
                django_track.delete()

        logging.info(f'track list generated successfully: {len(_files)} tracks found')
        print(f'track list generated successfully: {len(_files)} tracks found')
    ############################################

