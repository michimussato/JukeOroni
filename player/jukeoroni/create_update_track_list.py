import os
import logging
from player.jukeoroni.discogs import get_client, get_artist, get_album
from player.models import Artist, Album, Track as DjangoTrack
from player.jukeoroni.settings import (
    GLOBAL_LOGGING_LEVEL,
    MUSIC_DIR,
    AUDIO_FILES,
    ALBUM_TYPE_MUSIC,
)


LOG = logging.getLogger(__name__)
LOG.setLevel(GLOBAL_LOGGING_LEVEL)


def create_update_track_list():
    # TODO: filter image files, m3u etc.
    LOG.info('Generating updated track list...')
    discogs_client = get_client()
    _files = []
    _albums = []
    _artists = []
    for path, dirs, files in os.walk(MUSIC_DIR):
        # if not self.on:
        #     LOG.warning('JukeBox is turned off.')
        #     return

        # Remove part of path that can be retrieved from settings (MUSIC_DIR)
        # MUSIC_DIR:  /data/usb_hdd/media/audio/music
        # path:       /data/usb_hdd/media/audio/music/on_device/HIM - 2008 - Razorblade Romance [DSD128]/
        _path = os.path.relpath(path, MUSIC_DIR)
        # _path =
        album = os.path.basename(_path)
        try:
            # TODO: maybe use a better character
            artist, year, title = album.split(' - ')
        except ValueError:
            # with open(FAULTY_ALBUMS, 'a+') as f:
            #     f.write(album + '\n')
            # TODO: store this somewhere to fix it
            LOG.exception(f'Not a valid album path: {album}:')
            continue


        # COVER ARTIST
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
        if os.path.exists(os.path.join(MUSIC_DIR, jpg_path)):
            img_path = jpg_path
        elif os.path.exists(os.path.join(MUSIC_DIR, png_path)):
            img_path = png_path
        else:
            # with open(MISSING_COVERS_FILE, 'a+') as f:
            #     f.write(cover_root + '\n')
            LOG.info(f'cover is None: {album}')
            img_path = None

        # need to add artist too
        cover_online = None
        title_stripped = title.split(' [')[0]
        query_album = Album.objects.filter(artist=model_artist, album_title__exact=title, year__exact=year)


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

            if not query_album[0].album_type == ALBUM_TYPE_MUSIC:
                query_album.update(album_type=ALBUM_TYPE_MUSIC)

        else:
            cover_online = get_album(discogs_client, artist, title_stripped)
            model_album = Album(artist=model_artist, album_title=title, year=year, cover=img_path, cover_online=cover_online, album_type=ALBUM_TYPE_MUSIC)
            LOG.info(f'Album {model_album} not found in DB.')

        try:
            model_album.save()
            _albums.append(album)
            LOG.info(f'Album {model_album} correctly saved in DB.')
        except Exception:
            LOG.exception(f'Cannot save album model {title} by {artist}:')
        # COVER ALBUM


        for _file in files:
            if os.path.splitext(_file)[1] in AUDIO_FILES:
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

    # remove obsolete db objects:
    django_tracks = DjangoTrack.objects.all()
    for django_track in django_tracks:
        if django_track.audio_source not in _files:
            LOG.info(f'Removing track from DB: {django_track}')
            django_track.delete()
            LOG.info(f'Track removed from DB: {django_track}')

    django_albums = Album.objects.all()
    for django_album in django_albums:
        occurrences = [i for i in _albums if str(django_album.album_title).lower() in i.lower()]
        if len(occurrences) == 0:
            LOG.info(f'Removing album from DB: {django_album}')
            django_album.delete()
            LOG.info(f'Album removed from DB: {django_album}')

    django_artists = Artist.objects.all()
    for django_artist in django_artists:
        if django_artist.name not in _artists:
            LOG.info(f'Removing artist from DB: {django_artist}')
            django_artist.delete()

            """
AC/DC on OSX (HFS)
ACDC on /data/usb_hdd and AC:DC on /data/googledrive

Dec 19 09:25:01 jukeoroni gunicorn[18042]: Exception in thread Track List Generator Process:
Dec 19 09:25:01 jukeoroni gunicorn[18042]: Traceback (most recent call last):
Dec 19 09:25:01 jukeoroni gunicorn[18042]:   File "/usr/lib/python3.7/threading.py", line 917, in _bootstrap_inner
Dec 19 09:25:01 jukeoroni gunicorn[18042]:     self.run()
Dec 19 09:25:01 jukeoroni gunicorn[18042]:   File "/usr/lib/python3.7/threading.py", line 865, in run
Dec 19 09:25:01 jukeoroni gunicorn[18042]:     self._target(*self._args, **self._kwargs)
Dec 19 09:25:01 jukeoroni gunicorn[18042]:   File "/data/django/jukeoroni/player/jukeoroni/juke_box.py", line 416, in track_list_generator_task
Dec 19 09:25:01 jukeoroni gunicorn[18042]:     self.create_update_track_list()
Dec 19 09:25:01 jukeoroni gunicorn[18042]:   File "/data/django/jukeoroni/player/jukeoroni/juke_box.py", line 562, in create_update_track_list
Dec 19 09:25:01 jukeoroni gunicorn[18042]:     django_artist.delete()
Dec 19 09:25:01 jukeoroni gunicorn[18042]:   File "/data/venv/lib/python3.7/site-packages/django/db/models/base.py", line 953, in delete
Dec 19 09:25:01 jukeoroni gunicorn[18042]:     collector.collect([self], keep_parents=keep_parents)
Dec 19 09:25:01 jukeoroni gunicorn[18042]:   File "/data/venv/lib/python3.7/site-packages/django/db/models/deletion.py", line 308, in collect
Dec 19 09:25:01 jukeoroni gunicorn[18042]:     set(chain.from_iterable(protected_objects.values())),
Dec 19 09:25:01 jukeoroni gunicorn[18042]: django.db.models.deletion.ProtectedError: ("Cannot delete some instances of model 'Artist' because they are referenced through protected foreign keys: 'Album.artist'.", {Back In Black (Master Series V) [DSD128]})
            """

            LOG.info(f'Artist removed from DB: {django_artist}')

    LOG.info(f'Finished: track list generated successfully: {len(_files)} tracks, {len(_albums)} albums and {len(_artists)} artists found')
############################################
