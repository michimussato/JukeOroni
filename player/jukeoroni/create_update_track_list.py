import os
import logging
from player.jukeoroni.discogs import get_client, get_artist, get_album
from player.models import Artist, Album, Track as DjangoTrack
from player.jukeoroni.settings import (
    GLOBAL_LOGGING_LEVEL,
    # MUSIC_DIR,
    AUDIO_FILES,
    ALBUM_TYPES,
    # ALBUM_TYPE_MUSIC,
)


LOG = logging.getLogger(__name__)
LOG.setLevel(GLOBAL_LOGGING_LEVEL)


DELIMITER = ' - '


def create_update_track_list(box, directory, album_type):
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
        # _path =
        album = os.path.basename(_path)
        try:
            # TODO: maybe use a better character
            artist, year, title = album.split(DELIMITER)
        except ValueError:
            # with open(FAULTY_ALBUMS, 'a+') as f:
            #     f.write(album + '\n')
            # TODO: store this somewhere to fix it
            LOG.exception(f'Not a valid album path: {album}:')
            continue


        # COVER ARTIST
        # Artist can participate in Music and Meditation
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

            # if not model_album.album_type == album_type:
            #     query_album.update(album_type=album_type)

        else:
            cover_online = get_album(discogs_client, artist, title_stripped)
            model_album = Album(artist=model_artist, album_title=title, year=year, cover=img_path, cover_online=cover_online, album_type=album_type)
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
            # print
            # occurrences = list()
            # for _album in _albums:
            #     if str(django_album.album_title).lower() in str(_album).lower():
            #         occurrences.append(_album)
            #         LOG.debug(f'Album found in DB: {_album}')
            # # occurrences = [i for i in _albums if str(django_album.album_title).lower() in i.lower()]
            # LOG.debug(f'Occurrences in DB: {occurrences}')
            # if not bool(occurrences):
            LOG.info(f'Removing album from DB: {DELIMITER.join([django_album.artist.name, django_album.year, django_album.album_title])}')
            # Sacred Alliance [DSD][64] (Sacred Alliance [DSD][64])

            # LOG.debug(f'albums: {_albums}')
            # LOG.debug(f'{DELIMITER.join([django_album.artist.name, django_album.year, django_album.album_title]) not in _albums}')
            # 'Anima - 2014 - Sacred Alliance [DSD][64]'
            # Artist
            django_album.delete()
            LOG.info(f'Album removed from DB: {django_album}')

        """
Jan 14 20:19:45 jukeoroni gunicorn[4161]: [01-14-2022 20:19:45] [INFO] [Track List Generator Process (jukebox)|2950689888] [player.jukeoroni.create_update_track_list]: Removing album from DB: Motörhead [FLAC][24][192]
Jan 14 20:19:45 jukeoroni gunicorn[4161]: Exception in thread Track List Generator Process (jukebox):
Jan 14 20:19:45 jukeoroni gunicorn[4161]: Traceback (most recent call last):
Jan 14 20:19:45 jukeoroni gunicorn[4161]:   File "/usr/lib/python3.7/threading.py", line 917, in _bootstrap_inner
Jan 14 20:19:45 jukeoroni gunicorn[4161]:     self.run()
Jan 14 20:19:45 jukeoroni gunicorn[4161]:   File "/usr/lib/python3.7/threading.py", line 865, in run
Jan 14 20:19:45 jukeoroni gunicorn[4161]:     self._target(*self._args, **self._kwargs)
Jan 14 20:19:45 jukeoroni gunicorn[4161]:   File "/data/django/jukeoroni/player/jukeoroni/base_box.py", line 183, in track_list_generator_task
Jan 14 20:19:45 jukeoroni gunicorn[4161]:     create_update_track_list(box=self, directory=self.audio_dir, album_type=self.album_type)
Jan 14 20:19:45 jukeoroni gunicorn[4161]:   File "/data/django/jukeoroni/player/jukeoroni/create_update_track_list.py", line 164, in create_update_track_list
Jan 14 20:19:45 jukeoroni gunicorn[4161]:     django_album.delete()
Jan 14 20:19:45 jukeoroni gunicorn[4161]:   File "/data/venv/lib/python3.7/site-packages/django/db/models/base.py", line 953, in delete
Jan 14 20:19:45 jukeoroni gunicorn[4161]:     collector.collect([self], keep_parents=keep_parents)
Jan 14 20:19:45 jukeoroni gunicorn[4161]:   File "/data/venv/lib/python3.7/site-packages/django/db/models/deletion.py", line 308, in collect
Jan 14 20:19:45 jukeoroni gunicorn[4161]:     set(chain.from_iterable(protected_objects.values())),
Jan 14 20:19:45 jukeoroni gunicorn[4161]: django.db.models.deletion.ProtectedError: ("Cannot delete some instances of model 'Album' because they are referenced through protected foreign keys: 'Track.album'.", {on_device/Motörhead - 1977 - Motörhead [FLAC][24][192]/01 Motorhead.flac, on_device/Motörhead - 1977 - Motörhead [FLAC][24][192]/02 Over The Top.flac})
        """

    # django_artists = Artist.objects.all()
    # # Todo: need to add some logic to consider only album_type-specific artists, although
    # #  one artist can occur in music and medititation albums at the same time
    #
    # # Is it really necessary to delete artists? They could actually remain inside the DB without side effects most likely
    # for django_artist in django_artists:
    #
    #     if django_artist.name not in _artists:
    #         LOG.info(f'Removing artist from DB: {django_artist}')
    #         try:
    #             django_artist.delete()
    #             LOG.info(f'Artist removed from DB: {django_artist}')
    #         except Exception:
    #             LOG.exception(f'Could not delete Artist from DB: {django_artist}')
    #             # Is the artist connected to albums of other album_types?
    #             # _album_types = ALBUM_TYPES
    #             # _album_types.pop(album_type)
    #             #
    #             # for _album_type in _album_types:
    #             #     LOG.info(f'Artist is connected to album')


    LOG.info(f'Finished: {album_type} track list generated successfully: {len(_files)} tracks, {len(_albums)} albums and {len(_artists)} artists found')
############################################
