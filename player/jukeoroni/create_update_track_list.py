import os
import logging
import time

from django.db.models.deletion import ProtectedError
from django.db.utils import OperationalError
from player.jukeoroni.discogs import get_client, get_artist, get_album
from player.models import Artist, Album, Track as DjangoTrack
from player.jukeoroni.settings import Settings


LOG = logging.getLogger(__name__)
LOG.setLevel(Settings.GLOBAL_LOGGING_LEVEL)


# TODO: maybe use a better character
DELIMITER = ' - '


# TODO: use metadata in the future
#  https://stackoverflow.com/questions/51303424/pytaglib-taglib-dsd-dsf-format


def create_update_track_list(box, directory, album_type, file_filter):
    """

    Args:
        box: BaseBox object
        directory: full path, i. e.: /data/usb_hdd/media/audio/music. path can contain subdirectories that contain album directies
        album_type: music, audiobook or meditation
    """

    # TODO: filter image files, m3u etc.
    box.LOG.info(f'Generating updated track list for {box.box_type} ({directory})...')
    discogs_client = get_client()
    _files = []
    _albums = []
    _artists = []
    for path, dirs, files in os.walk(directory):
        # Remove part of path that can be retrieved from settings (MUSIC_DIR)
        # MUSIC_DIR:  /data/usb_hdd/media/audio/music
        # path:       /data/usb_hdd/media/audio/music/on_device/HIM - 2008 - Razorblade Romance [DSD128]/
        _path = os.path.relpath(path, directory)
        album = os.path.basename(_path)
        try:
            artist, year, title = album.split(DELIMITER)
        except ValueError:
            LOG.exception(f'Not a valid album path: {album}:')
            continue

        # COVER ARTIST
        # Artist can participate in any box library
        cover_online = None
        # TODO: if str(artist).lower() != 'soundtrack':  # Soundtracks have different artists, so no need to add artist cover
        query_artist = Artist.objects.filter(name__exact=artist)
        # TODO: maybe objects.get() is better because artist name is unique
        if bool(query_artist):
            LOG.info(f'Artist {query_artist} found in db...')
            model_artist = query_artist[0]  # name is unique, so index 0 is the correct model
            # if str(model_artist.name).lower() != 'soundtrack':
            if model_artist.cover_online is None:
                LOG.info(f'No online cover for artist {model_artist} defined. Trying to get one...')
                cover_online = get_artist(discogs_client, artist)
                if cover_online:
                    model_artist.cover_online = cover_online
                    model_artist.save()
        else:
            LOG.info(f'Artist {artist} not found in db; creating new entry...')
            cover_online = get_artist(discogs_client, artist)
            model_artist = Artist(name=artist, cover_online=cover_online)
            model_artist.save()

        if artist not in _artists:
            _artists.append(artist)
        # COVER ARTIST

        cover_root = _path
        jpg_path = os.path.join(cover_root, 'cover.jpg')
        png_path = os.path.join(cover_root, 'cover.png')
        if os.path.exists(os.path.join(directory, jpg_path)):
            img_path = jpg_path
        elif os.path.exists(os.path.join(directory, png_path)):
            img_path = png_path
        else:
            LOG.error(f'Missing cover: cover is None for album {album}')
            img_path = None

        # need to add artist too
        cover_online = None
        title_stripped = title.split(' [')[0]
        query_album = Album.objects.filter(artist=model_artist, album_title__exact=title, year__exact=year, album_type=album_type)

        # COVER ALBUM
        if bool(query_album):
            model_album = query_album[0]
            LOG.info(f'Album {model_album} found in DB.')
            model_album.cover = img_path
            if model_album.cover_online is None:
                LOG.info(f'No online cover for album {model_album} defined. Trying to get one...')
                cover_online = get_album(discogs_client, artist, title_stripped)
                if cover_online:
                    model_album.cover_online = cover_online
                else:
                    LOG.info('Could not find an online cover.')

        else:
            cover_online = get_album(discogs_client, artist, title_stripped)
            model_album = Album(artist=model_artist, album_title=title, year=year, cover=img_path, cover_online=cover_online, album_type=album_type)
            LOG.info(f'Album {model_album} not found in DB.')

        attempts = 0
        while attempts < Settings.DB_SAVE_ATTEMPTS:
            try:
                model_album.save()
                _albums.append(album)
                LOG.info(f'Album {model_album} correctly saved in DB.')
                break
            except OperationalError:
                attempts += 1
                LOG.exception(f'Cannot save album model {title} by {artist} (attempt {attempts} of {Settings.DB_SAVE_ATTEMPTS}):')
                time.sleep(Settings.DB_SAVE_WAIT_BETWEEN_ATTEMPTS)
                """
    [08-30-2022 09:43:10] [ERROR   ] [Track List Generator Thread (meditationbox)|2916086880], File "/data/django/jukeoroni/player/jukeoroni/create_update_track_list.py", line 113, in create_update_track_list:    Cannot save album model Sea of Dreams (Philippe De Canck) [FLAC][16][44.1] by Sounds of Nature (Serenity Series):
    Traceback (most recent call last):
      File "/data/venv/lib/python3.7/site-packages/django/db/backends/utils.py", line 84, in _execute
        return self.cursor.execute(sql, params)
      File "/data/venv/lib/python3.7/site-packages/django/db/backends/sqlite3/base.py", line 423, in execute
        return Database.Cursor.execute(self, query, params)
    sqlite3.OperationalError: database is locked
    
    The above exception was the direct cause of the following exception:
    
    Traceback (most recent call last):
      File "/data/django/jukeoroni/player/jukeoroni/create_update_track_list.py", line 109, in create_update_track_list
        model_album.save()
      File "/data/venv/lib/python3.7/site-packages/django/db/models/base.py", line 727, in save
        force_update=force_update, update_fields=update_fields)
      File "/data/venv/lib/python3.7/site-packages/django/db/models/base.py", line 765, in save_base
        force_update, using, update_fields,
      File "/data/venv/lib/python3.7/site-packages/django/db/models/base.py", line 846, in _save_table
        forced_update)
      File "/data/venv/lib/python3.7/site-packages/django/db/models/base.py", line 899, in _do_update
        return filtered._update(values) > 0
      File "/data/venv/lib/python3.7/site-packages/django/db/models/query.py", line 802, in _update
        return query.get_compiler(self.db).execute_sql(CURSOR)
      File "/data/venv/lib/python3.7/site-packages/django/db/models/sql/compiler.py", line 1559, in execute_sql
        cursor = super().execute_sql(result_type)
      File "/data/venv/lib/python3.7/site-packages/django/db/models/sql/compiler.py", line 1175, in execute_sql
        cursor.execute(sql, params)
      File "/data/venv/lib/python3.7/site-packages/django/db/backends/utils.py", line 98, in execute
        return super().execute(sql, params)
      File "/data/venv/lib/python3.7/site-packages/django/db/backends/utils.py", line 66, in execute
        return self._execute_with_wrappers(sql, params, many=False, executor=self._execute)
      File "/data/venv/lib/python3.7/site-packages/django/db/backends/utils.py", line 75, in _execute_with_wrappers
        return executor(sql, params, many, context)
      File "/data/venv/lib/python3.7/site-packages/django/db/backends/utils.py", line 84, in _execute
        return self.cursor.execute(sql, params)
      File "/data/venv/lib/python3.7/site-packages/django/db/utils.py", line 90, in __exit__
        raise dj_exc_value.with_traceback(traceback) from exc_value
      File "/data/venv/lib/python3.7/site-packages/django/db/backends/utils.py", line 84, in _execute
        return self.cursor.execute(sql, params)
      File "/data/venv/lib/python3.7/site-packages/django/db/backends/sqlite3/base.py", line 423, in execute
        return Database.Cursor.execute(self, query, params)
    django.db.utils.OperationalError: database is locked
                """

        # COVER ALBUM

        for _file in files:
            if os.path.splitext(_file)[1] in file_filter:
                file_path = os.path.join(_path, _file)
                query_track = DjangoTrack.objects.filter(audio_source__exact=file_path)
                if len(query_track) > 1:
                    LOG.warning(f'Track in DB multiple times: {file_path}')
                    for track in query_track:
                        track.delete()
                        LOG.warning(f'Track deleted: {track}')
                    query_track = []
                if len(query_track) == 1:
                    LOG.info(f'Track found in DB: {query_track}')
                    _edit = False
                    if not query_track[0].album == model_album:
                        query_track.update(album=model_album)
                        LOG.info('Track album updated in DB: {0}'.format(query_track[0]))
                    if not query_track[0].track_title == _file:
                        query_track.update(track_title=_file)
                        LOG.info('Track track_title updated in DB: {0}'.format(query_track[0]))
                else:
                    model_track = DjangoTrack.objects.create(album=model_album, audio_source=file_path, track_title=_file)
                    LOG.info('Track created in DB: {0}'.format(model_track))

                _files.append(file_path)

    # TODO:
    #  Maybe we blow the DB with the box_type check...
    #  let's see...

    # remove obsolete db objects:
    django_tracks = DjangoTrack.objects.filter(album__album_title=album_type)
    for django_track in django_tracks:
        if django_track.audio_source not in _files:  # and django_track.album.album_type == album_type:
            LOG.info(f'Removing track from DB: {django_track}')
            django_track.delete()
            LOG.info(f'Track removed from DB: {django_track}')

    django_albums = Album.objects.filter(album_type=album_type)
    for django_album in django_albums:
        if DELIMITER.join([django_album.artist.name, django_album.year, django_album.album_title]) not in _albums:
            LOG.info(f'Removing album from DB: {DELIMITER.join([django_album.artist.name, django_album.year, django_album.album_title])}')
            django_album.delete()
            LOG.info(f'Album removed from DB: {django_album}')

    # no special logic required. if artist is still connected, it
    # cannot be deleted
    django_artists = Artist.objects.all()
    for django_artist in django_artists:
        try:
            django_artist.delete()
            LOG.info(f'Artist removed from DB: {django_artist}')
        except ProtectedError:
            LOG.debug(f'Artist {django_artist} is still connected (in use). Ignored...')

    LOG.info(f'Finished: {album_type} track list generated successfully: {len(_files)} tracks, {len(_albums)} albums and {len(_artists)} artists found')
############################################
